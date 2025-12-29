import os
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ExcelImportService:
    """Service for importing Excel files into the Acts table"""
    
    def __init__(self, imports_folder: str = "app/imports"):
        self.imports_folder = Path(imports_folder)
        self.processed_folder = self.imports_folder / "processed"
        self.failed_folder = self.imports_folder / "failed"
        
        # Ensure folders exist
        self.imports_folder.mkdir(exist_ok=True)
        self.processed_folder.mkdir(exist_ok=True)
        self.failed_folder.mkdir(exist_ok=True)

    def scan_imports_folder(self) -> List[Path]:
        """Scan the imports folder for Excel files"""
        excel_files = []
        
        # Look for .xlsx and .xls files
        for pattern in ['*.xlsx', '*.xls']:
            excel_files.extend(self.imports_folder.glob(pattern))
        
        # Filter out files in subdirectories
        excel_files = [f for f in excel_files if f.parent == self.imports_folder]
        
        logger.info(f"Found {len(excel_files)} Excel file(s) in {self.imports_folder}")
        return excel_files

    def parse_excel_file(self, file_path: Path) -> pd.DataFrame:
        """
        Parse an Excel file and return a DataFrame.
        Handles both .xlsx and .xls formats.
        The Excel has headers at row 1 (0-indexed), so we skip the first row.
        """
        try:
            # Read Excel file with header at row 1 (skip first row which is empty/NaN)
            df = pd.read_excel(
                file_path, 
                engine='openpyxl' if file_path.suffix == '.xlsx' else None,
                header=1  # Header is at row index 1
            )
            
            # Normalize column names
            column_mapping = {
                'SL.No': 'sl_no',
                'State': 'state',
                'Industry': 'industry',
                'Company Type and Specific Acts applicable for Each type of Company': 'company_type',
                'Legislative Area': 'legislative_area',
                'Central Acts & Rules': 'central_acts',
                'State Specific Acts & Rules': 'state_acts',
                'Employee Applicability': 'employee_applicability'
            }
            
            # Rename columns to match database schema
            df.rename(columns=column_mapping, inplace=True)
            
            # Drop rows where all values are NaN
            df.dropna(how='all', inplace=True)
            
            # Handle merged cells by forward-filling values
            # In Excel, merged cells only have value in the first row, rest are NaN
            # We need to fill these NaN values with the previous non-NaN value
            columns_to_fill = ['state', 'industry', 'company_type', 'legislative_area', 
                              'central_acts', 'state_acts', 'employee_applicability']
            
            for col in columns_to_fill:
                if col in df.columns:
                    df[col] = df[col].ffill()
            
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
        expected_columns = ['sl_no', 'state', 'industry', 'company_type', 
                          'legislative_area', 'central_acts', 'state_acts', 
                          'employee_applicability']
        
        # Check for expected columns
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            return False, f"Missing expected columns: {', '.join(missing_columns)}"
        
        # Check for at least some non-null data in key columns
        key_columns = ['state', 'industry']
        has_data = False
        for col in key_columns:
            if df[col].notna().sum() > 0:
                has_data = True
                break
        
        if not has_data:
            return False, "No valid data found in key columns (state, industry)"
        
        return True, ""

    def transform_dataframe_to_acts(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Transform DataFrame rows into Acts model dictionaries.
        Maps Excel columns to database fields, excluding sl_no.
        """
        # Database columns (excluding sl_no which we don't need)
        db_columns = ['state', 'industry', 'company_type', 'legislative_area', 
                     'central_acts', 'state_acts', 'employee_applicability']
        
        acts_data = []
        
        for _, row in df.iterrows():
            # Skip completely empty rows
            if row.isna().all():
                continue
            
            act_dict = {}
            
            for col in db_columns:
                if col not in df.columns:
                    continue
                    
                value = row[col]
                
                # Convert NaN to None
                if pd.isna(value):
                    value = None
                # Convert values to string and strip whitespace
                elif value is not None and isinstance(value, str):
                    value = value.strip()
                
                act_dict[col] = value
            
            # Only add if we have at least state or industry
            if act_dict.get('state') or act_dict.get('industry'):
                acts_data.append(act_dict)
        
        logger.info(f"Transformed {len(acts_data)} valid acts from DataFrame")
        return acts_data

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
            
            # Transform to acts data
            acts_data = self.transform_dataframe_to_acts(df)
            
            if not acts_data:
                return False, "No valid records found after transformation", 0
            
            return True, "Data parsed successfully", len(acts_data)
            
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {str(e)}"
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
        return {
            'pending': len(self.scan_imports_folder()),
            'processed': len(list(self.processed_folder.glob('*.xls*'))),
            'failed': len(list(self.failed_folder.glob('*.xls*')))
        }
