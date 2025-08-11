# data_process_pro_v3.py
#
# Production-Grade Data Processing Pipeline for Vahan Registration Data
#
# Author: 5-Year Experienced Data Professional
# Date: 2025-08-11
#
# This version fixes errors related to complex multi-level headers in the source
# files by using a more robust, position-based column identification strategy.
#
# Key Features:
# - DRY Principle: A single, generic function handles all file processing.
# - Positional Column Finding: Intelligently locates data blocks and columns by position.
# - Data Validation: Asserts data quality before saving the final output.
# - Centralized Configuration: Easily manage and add new data sources.
# - Command-Line Interface: Flexible execution via command-line arguments.

import pandas as pd
from pathlib import Path
import logging
import argparse
from typing import List, Dict, Any, Optional

# --- 1. Configuration & Setup ---
# Configure professional-grade logging.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-8s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# --- 2. Core Processing Functions ---

def find_start_row(df: pd.DataFrame, keyword: str = 'S No') -> int:
    """
    Robustly inspects a dataframe to find the row where the actual data starts.
    Handles case-insensitivity and whitespace.
    """
    for i, row in df.iterrows():
        try:
            # The data starts on the row immediately after the header row with 'S No'.
            if keyword.lower() in str(row.iloc[0]).lower().strip():
                return i + 1
        except IndexError:
            continue
    logging.warning(f"Header keyword '{keyword}' not found. Assuming data starts at row 1.")
    return 1

def process_source_file(file_path: Path, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    A generic and robust function to load and transform a single source file.
    This version uses positional logic to handle messy headers.
    
    Args:
        file_path (Path): The path to the Excel file.
        config (Dict): A dictionary containing processing configuration for the file.
        
    Returns:
        Optional[pd.DataFrame]: A tidy DataFrame or None if processing fails.
    """
    try:
        logging.info(f"Processing source: {file_path.name}")
        
        if not file_path.exists():
            logging.error(f"File not found: {file_path}")
            return None

        # Load the entire sheet first to find the data's starting point
        df_raw = pd.read_excel(file_path, header=None)
        start_row_index = find_start_row(df_raw)
        
        # Reload the dataframe starting from the actual data
        df = pd.read_excel(file_path, header=None, skiprows=start_row_index)
        
        # --- Positional Column Identification (More Robust) ---
        # Drop the first column (S No) and the last column (Total)
        df = df.drop(columns=[df.columns[0], df.columns[-1]], errors='ignore')
        
        # The first column in the remaining dataframe is always the entity name
        entity_col_index = df.columns[0]
        df.rename(columns={entity_col_index: 'entity_name'}, inplace=True)
        
        logging.info(f"Identified entity column as: 'entity_name' (positional).")

        # --- Data Transformation (Wide to Tidy) ---
        id_vars = ['entity_name']
        value_vars = [col for col in df.columns if col not in id_vars]
        
        df_tidy = df.melt(
            id_vars=id_vars,
            value_vars=value_vars,
            var_name='vehicle_class_col_id',
            value_name='registrations'
        )
        
        # Add the entity type from the config
        df_tidy['entity_type'] = config['entity_type']
        
        # --- Data Validation ---
        assert not df_tidy.empty, "Melt operation resulted in an empty DataFrame."
        assert 'registrations' in df_tidy.columns, "Missing 'registrations' column."
        
        logging.info(f"Successfully processed {len(df_tidy)} records from {file_path.name}.")
        return df_tidy

    except Exception as e:
        logging.error(f"Failed to process file {file_path.name}. Error: {e}", exc_info=True)
        return None


# --- 3. Main Execution Block ---

def main(input_dir: Path, output_dir: Path):
    """
    Main function to orchestrate the data processing pipeline.
    """
    logging.info("--- Starting Vahan Data Processing Pipeline ---")
    
    # --- Centralized Source Configuration ---
    SOURCES = [
        {
            "file_name": "reportTable.xlsx",
            "entity_type": "Maker"
        },
        {
            "file_name": "reportTable (1).xlsx",
            "entity_type": "Vehicle Category"
        }
    ]
    
    all_dfs = []
    for source_config in SOURCES:
        file_path = input_dir / source_config["file_name"]
        processed_df = process_source_file(file_path, source_config)
        if processed_df is not None:
            all_dfs.append(processed_df)
            
    if not all_dfs:
        logging.error("No dataframes were processed. Exiting pipeline.")
        return

    # Combine all processed dataframes
    logging.info("Combining all processed data sources...")
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # --- Final Cleaning & Validation ---
    combined_df['entity_name'] = combined_df['entity_name'].str.strip()
    combined_df.dropna(subset=['registrations'], inplace=True)
    combined_df['registrations'] = pd.to_numeric(combined_df['registrations'], errors='coerce').fillna(0)
    combined_df = combined_df[combined_df['registrations'] > 0].copy()
    combined_df['registrations'] = combined_df['registrations'].astype(int)
    
    # Final check
    assert not combined_df.empty, "Final combined dataframe is empty after cleaning."
    
    # --- Save Output ---
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "vahan_processed_tidy.csv"
    
    combined_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    logging.info(f"✅ Pipeline complete! Processed {len(combined_df)} total valid records.")
    logging.info(f"Final tidy dataset saved to: {output_path}")


if __name__ == "__main__":
    # --- Command-Line Interface Setup ---
    # This allows the script to be run with flexible paths, e.g.:
    # python data_process_pro_v3.py --input data/raw --output data/processed
    
    parser = argparse.ArgumentParser(description="Vahan Data Processing Pipeline.")
    
    # Set default paths relative to the current working directory
    default_input = Path.cwd() / "data" / "raw"
    default_output = Path.cwd() / "data" / "processed"
    
    parser.add_argument(
        '--input', 
        type=Path, 
        default=default_input,
        help=f"Input directory containing raw Excel files. Defaults to: {default_input}"
    )
    parser.add_argument(
        '--output', 
        type=Path, 
        default=default_output,
        help=f"Output directory to save the processed CSV. Defaults to: {default_output}"
    )
    
    args = parser.parse_args()
    
    main(input_dir=args.input, output_dir=args.output)
