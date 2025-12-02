import logging
import pandas as pd
import re
from .models import RawDataset

logger = logging.getLogger(__name__)


class DatasetIntrospectionService:
    """
    Reads the CSV header and returns normalized column names so the
    user can classify them into intervention/object types manually.
    """

    def __init__(self, preview_rows: int = 5):
        self.preview_rows = preview_rows

    def analyze_dataset(self, dataset: RawDataset) -> dict:
        try:
            # Use file.open() for GCS compatibility (works for both local and GCS)
            with dataset.file.open('rb') as f:
                df = pd.read_csv(f, nrows=self.preview_rows)
            original_columns = list(df.columns)
            normalized_columns = self._normalize_columns(original_columns)

            result = {"columns": normalized_columns}
            dataset.column_mapping = result
            dataset.status = 'ANALYZED'
            dataset.error_message = ''
            dataset.save()
            return result
        except Exception as exc:
            dataset.status = 'FAILED'
            dataset.error_message = str(exc)
            dataset.save()
            logger.exception("Dataset introspection failed for %s", dataset.id)
            raise

    def _normalize_columns(self, columns):
        seen = set()
        normalized = []

        for idx, name in enumerate(columns):
            base = self._slugify(name)
            if not base:
                base = f"column_{idx+1}"

            candidate = base
            counter = 1
            while candidate in seen:
                counter += 1
                candidate = f"{base}_{counter}"

            seen.add(candidate)
            normalized.append({
                "original": name,
                "variable": candidate
            })

        return normalized

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r'[^a-z0-9]+', '_', value)
        value = re.sub(r'_+', '_', value)
        return value.strip('_')

class ETLService:
    def ingest_dataset(self, dataset: RawDataset):
        """
        Reads the CSV and ingests data into UnifiedObject and UnifiedTimeSeries
        based on the dataset.column_mapping.
        
        Logic:
        - If 'id' values are unique → Snapshot (static data)
        - If 'id' values repeat → Time Series data
        """
        try:
            mapping = dataset.column_mapping
            # Use file.open() for GCS compatibility (works for both local and GCS)
            with dataset.file.open('rb') as f:
                df = pd.read_csv(f)
            
            # Helper to get value or None
            def get_val(row, col_name):
                if not col_name or col_name not in row:
                    return None
                val = row[col_name]
                return val if pd.notna(val) else None

            # Extract core field mappings
            id_col = mapping.get('id')
            lat_col = mapping.get('latitude')
            lon_col = mapping.get('longitude')
            ts_col = mapping.get('timestamp')
            val_col = mapping.get('value')
            
            if not id_col:
                raise ValueError("'id' column mapping is required")
            
            # Detect dataset type: check if ID values are unique
            id_values = df[id_col].dropna()
            is_snapshot = len(id_values) == len(id_values.unique())
            
            from .models import UnifiedObject, UnifiedTimeSeries, MetricCatalog
            
            if is_snapshot:
                # SNAPSHOT: Each row is a unique object with static data
                for index, row in df.iterrows():
                    external_id = str(get_val(row, id_col))
                    
                    # Extract extra data (everything except core fields)
                    extra_data = {}
                    if 'extra_cols' in mapping:
                        for col in mapping['extra_cols']:
                            extra_data[col] = get_val(row, col)
                    
                    # Also include value in extra_data if present (for snapshot)
                    if val_col and get_val(row, val_col) is not None:
                        extra_data['_snapshot_value'] = get_val(row, val_col)

                    UnifiedObject.objects.update_or_create(
                        project=dataset.project,
                        external_id=external_id,
                        defaults={
                            'latitude': float(get_val(row, lat_col)),
                            'longitude': float(get_val(row, lon_col)),
                            'extra_data': extra_data
                        }
                    )
            
            else:
                # TIME SERIES: Multiple rows per ID
                # First, ensure all objects exist
                unique_ids = id_values.unique()
                for ext_id in unique_ids:
                    # Find first row with this ID to get lat/lon
                    first_row = df[df[id_col] == ext_id].iloc[0]
                    
                    extra_data = {}
                    if 'extra_cols' in mapping:
                        for col in mapping['extra_cols']:
                            val = get_val(first_row, col)
                            if val is not None:
                                extra_data[col] = val
                    
                    UnifiedObject.objects.update_or_create(
                        project=dataset.project,
                        external_id=str(ext_id),
                        defaults={
                            'latitude': float(get_val(first_row, lat_col)),
                            'longitude': float(get_val(first_row, lon_col)),
                            'extra_data': extra_data
                        }
                    )
                
                # Now ingest time series data
                metric, _ = MetricCatalog.objects.get_or_create(
                    id='default_metric', 
                    defaults={'name': 'Default Metric', 'unit': 'units'}
                )

                ts_objects = []
                for index, row in df.iterrows():
                    external_id = str(get_val(row, id_col))
                    
                    # Find the object
                    try:
                        obj = UnifiedObject.objects.get(project=dataset.project, external_id=external_id)
                    except UnifiedObject.DoesNotExist:
                        continue

                    # Extract extra data for this reading
                    extra_data = {}
                    if 'extra_cols' in mapping:
                        for col in mapping['extra_cols']:
                            extra_data[col] = get_val(row, col)
                            
                    ts_objects.append(UnifiedTimeSeries(
                        project=dataset.project,
                        object=obj,
                        timestamp=pd.to_datetime(get_val(row, ts_col)),
                        value=float(get_val(row, val_col)),
                        metric=metric,
                        extra_data=extra_data
                    ))
                    
                    # Batch create every 1000 rows
                    if len(ts_objects) >= 1000:
                        UnifiedTimeSeries.objects.bulk_create(ts_objects)
                        ts_objects = []
                
                if ts_objects:
                    UnifiedTimeSeries.objects.bulk_create(ts_objects)

            dataset.status = 'INGESTED'
            dataset.save()

        except Exception as e:
            dataset.status = 'FAILED'
            dataset.error_message = str(e)
            dataset.save()
            raise e
