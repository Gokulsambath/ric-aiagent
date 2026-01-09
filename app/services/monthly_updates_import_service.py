import os
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging
from app.repository.monthly_updates_repo import MonthlyUpdates

logger = logging.getLogger(__name__)

class MonthlyUpdatesImportService:
    """Service for importing Monthly Updates Excel files"""
    
    def __init__(self, imports_folder: str = "app/imports"):
        self.imports_folder = Path(imports_folder)
        self.processed_folder = self.imports_folder / "processed"
        self.failed_folder = self.imports_folder / "failed"
        
        # Ensure folders exist
        self.imports_folder.mkdir(exist_ok=True)
        self.processed_folder.mkdir(exist_ok=True)
        self.failed_folder.mkdir(exist_ok=True)

    def scan_monthly_updates_files(self) -> List[Path]:
        """Scan the imports folder for monthly updates Excel files"""
        excel_files = []
        
        # Look for files containing "Monthly Updates" in the name
        for pattern in ['*.xlsx', '*.xls']:
            all_files = self.imports_folder.glob(pattern)
            # Filter for monthly updates files
            excel_files.extend([f for f in all_files if 'monthly updates' in f.name.lower()])
        
        # Filter out files in subdirectories
        excel_files = [f for f in excel_files if f.parent == self.imports_folder]
        
        logger.info(f"Found {len(excel_files)} Monthly Updates Excel file(s) in {self.imports_folder}")
        return excel_files

    def parse_excel_file(self, file_path: Path) -> pd.DataFrame:
        """
        Parse a Monthly Updates Excel file and return a DataFrame.
        Expected columns: Sl No., Title, Category ID, Description, Change Type, State, Effective Date, Update Date, Source Link
        """
        try:
            # Read Excel file with first row as header (header=0 is default)
            df = pd.read_excel(
                file_path, 
                engine='openpyxl' if file_path.suffix == '.xlsx' else None,
                header=0
            )

            # Normalize DataFrame columns: collapse all whitespace and convert to lowercase
            # This handles 'Effective   Date' -> 'effective date'
            df.columns = [' '.join(str(c).split()).lower() for c in df.columns]
            
            # More flexible mapping to handle various column name formats (lowercase keys)
            column_mapping = {
                'sl no.': 'sl_no',
                'sl no': 'sl_no',
                's.no.': 'sl_no',
                'serial no': 'sl_no',
                'title': 'title',
                'update title': 'title',
                'category id': 'category',
                'category': 'category',
                'description': 'description',
                'details': 'description',
                'change type': 'change_type',
                'type': 'change_type',
                'update type': 'change_type',
                'state': 'state',
                'effective date': 'effective_date',
                'effective from': 'effective_date',
                'update date': 'update_date',
                'date': 'update_date',
                'source link': 'source_link',
                'link': 'source_link',
                'url': 'source_link'
            }
            
            # Rename columns to match database schema
            df.rename(columns=column_mapping, inplace=True)
            
            # Drop rows where all values are NaN
            df.dropna(how='all', inplace=True)
            
            logger.info(f"Parsed {file_path.name}: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
        except Exception as e:
            logger.error(f"Error parsing {file_path.name}: {str(e)}")
            raise

    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate the DataFrame has required columns and data.
        Returns (is_valid, error_message)
        """
        # Check if DataFrame is empty
        if df.empty:
            return False, "Excel file is empty"
        
        # Expected columns based on our schema
        required_columns = ['title', 'category', 'description', 'change_type', 
                          'state', 'effective_date', 'update_date']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Check for at least some non-null data in key columns
        key_columns = ['title', 'category', 'state']
        has_data = False
        for col in key_columns:
            if df[col].notna().sum() > 0:
                has_data = True
                break
        
        if not has_data:
            return False, "No valid data found in key columns (title, category, state)"
        
        return True, ""

    def transform_dataframe_to_updates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Transform DataFrame rows into MonthlyUpdate model dictionaries.
        Maps Excel columns to database fields, excluding sl_no.
        """
        # Database columns (excluding sl_no and id which are auto-generated)
        db_columns = ['title', 'category', 'description', 'change_type', 
                     'state', 'effective_date', 'update_date', 'source_link']
        
        updates_data = []
        
        for _, row in df.iterrows():
            # Skip completely empty rows
            if row.isna().all():
                continue
            
            update_dict = {}
            
            for col in db_columns:
                if col not in df.columns:
                    continue
                    
                value = row[col]
                
                # Handle date columns specially
                if col in ['effective_date', 'update_date']:
                    if pd.isna(value):
                        # Skip this row if date is missing
                        logger.warning(f"Skipping row due to missing {col}")
                        continue
                    # Convert to date object
                    try:
                        if isinstance(value, str):
                            value = pd.to_datetime(value).date()
                        elif isinstance(value, pd.Timestamp):
                            value = value.date()
                        elif hasattr(value, 'date'):
                            value = value.date()
                    except Exception as e:
                        logger.warning(f"Could not parse date {value}: {e}")
                        continue
                # Handle text columns
                elif pd.isna(value):
                    # For source_link, None is allowed
                    if col == 'source_link':
                        value = None
                    else:
                        # For other columns, skip if empty
                        logger.warning(f"Skipping row due to missing {col}")
                        continue
                elif isinstance(value, str):
                    value = value.strip()
                
                update_dict[col] = value
            
            # Only add if we have all required fields
            required_fields = ['title', 'category', 'description', 'change_type', 
                             'state', 'effective_date', 'update_date']
            
            # Check for missing fields
            missing = [f for f in required_fields if f not in update_dict or update_dict[f] is None]
            
            if not missing:
                updates_data.append(update_dict)
            else:
                logger.warning(f"Row skipped. Missing fields: {missing}")
        
        logger.info(f"Transformed {len(updates_data)} valid updates from DataFrame")
        return updates_data

    def process_import(self, file_path: Path) -> Tuple[bool, str, int]:
        """
        Process a single Excel file import.
        Returns (success, message, records_count)
        """
        try:
            logger.info(f"Processing import: {file_path.name}")
            
            # Parse Excel
            df = self.parse_excel_file(file_path)
            
            # Validate data
            is_valid, error_msg = self.validate_data(df)
            if not is_valid:
                logger.error(f"Validation failed for {file_path.name}: {error_msg}")
                return False, error_msg, 0
            
            # Transform to updates data
            updates_data = self.transform_dataframe_to_updates(df)
            
            if not updates_data:
                return False, "No valid records found after transformation", 0
            
            # Save to database (Persistence Logic)
            repo = MonthlyUpdates()
            count = repo.bulk_upsert(updates_data)
            
            logger.info(f"Successfully imported {count} records")
            return True, "Import successful", count
            
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0

    def process_excel_stream(self, file_content: bytes, filename: str) -> Tuple[bool, str, int]:
        """
        Process an Excel file from a byte stream (direct upload).
        Returns (success, message, records_count)
        """
        try:
            logger.info(f"Processing uploaded stream: {filename}")
            
            # Read Excel from bytes
            # pd.read_excel can accept a bytes object
            import io
            file_stream = io.BytesIO(file_content)
            
            df = pd.read_excel(
                file_stream, 
                engine='openpyxl' if filename.lower().endswith('.xlsx') else None,
                header=0
            )

            # Normalize DataFrame columns
            df.columns = [' '.join(str(c).split()).lower() for c in df.columns]
            
            # Column mapping
            column_mapping = {
                'sl no.': 'sl_no',
                'sl no': 'sl_no',
                's.no.': 'sl_no',
                'serial no': 'sl_no',
                'title': 'title',
                'update title': 'title',
                'category id': 'category',
                'category': 'category',
                'description': 'description',
                'details': 'description',
                'change type': 'change_type',
                'type': 'change_type',
                'update type': 'change_type',
                'state': 'state',
                'effective date': 'effective_date',
                'effective from': 'effective_date',
                'update date': 'update_date',
                'date': 'update_date',
                'source link': 'source_link',
                'link': 'source_link',
                'url': 'source_link'
            }
            
            df.rename(columns=column_mapping, inplace=True)
            df.dropna(how='all', inplace=True)
            
            logger.info(f"Parsed {filename}: {len(df)} rows, {len(df.columns)} columns")

            # Validate data
            is_valid, error_msg = self.validate_data(df)
            if not is_valid:
                logger.error(f"Validation failed for {filename}: {error_msg}")
                return False, error_msg, 0
            
            # Transform to updates data
            updates_data = self.transform_dataframe_to_updates(df)
            
            if not updates_data:
                return False, "No valid records found after transformation", 0
            
            # Save to database
            repo = MonthlyUpdates()
            count = repo.bulk_upsert(updates_data)
            
            logger.info(f"Successfully imported {count} records from {filename}")
            return True, "Import successful", count
            
        except Exception as e:
            error_msg = f"Error processing {filename}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0

    def archive_file(self, file_path: Path, success: bool) -> None:
        """
        Move processed file to appropriate folder (processed or failed).
        Adds timestamp to filename to avoid conflicts.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        if success:
            destination = self.processed_folder / new_filename
        else:
            destination = self.failed_folder / new_filename
        
        try:
            shutil.move(str(file_path), str(destination))
            logger.info(f"Archived {file_path.name} to {destination}")
        except Exception as e:
            logger.error(f"Error archiving {file_path.name}: {str(e)}")

    def get_import_stats(self) -> Dict[str, int]:
        """Get statistics about imports"""
        monthly_updates_files = [f for f in self.scan_monthly_updates_files()]
        return {
            'pending': len(monthly_updates_files),
            'processed': len([f for f in self.processed_folder.glob('*.xls*') if 'monthly updates' in f.name.lower()]),
            'failed': len([f for f in self.failed_folder.glob('*.xls*') if 'monthly updates' in f.name.lower()])
        }
