import os
import csv
import glob
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from gee_api.models import State, District, SubDistrict, Village
from typing import Dict, List, Optional
from django.conf import settings


class Command(BaseCommand):
    help = 'Populate the database with location data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='data/csv',
            help='Directory containing CSV files (default: data/csv)'
        )
        parser.add_argument(
            '--drop-existing',
            action='store_true',
            help='Drop all existing location data before populating'
        )
        parser.add_argument(
            '--drop-states',
            nargs='+',
            help='Drop data for specific states before populating (e.g., --drop-states punjab rajasthan)'
        )
        parser.add_argument(
            '--state',
            type=str,
            help='Process only specific state (use state name from CSV)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually inserting data'
        )

    def handle(self, *args, **options):
        csv_dir = options['csv_dir']
        drop_existing = options['drop_existing']
        drop_states = options['drop_states']
        specific_state = options['state']
        dry_run = options['dry_run']

        # Make csv_dir relative to project root if it's not absolute
        if not os.path.isabs(csv_dir):
            csv_dir = os.path.join(settings.BASE_DIR, csv_dir)

        if not os.path.exists(csv_dir):
            self.stdout.write(
                self.style.ERROR(f'CSV directory not found: {csv_dir}')
            )
            return

        # Find all CSV files in the directory
        csv_files = glob.glob(os.path.join(csv_dir, '*.csv'))
        if not csv_files:
            self.stdout.write(
                self.style.ERROR(f'No CSV files found in {csv_dir}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {len(csv_files)} CSV files for processing')
        )

        # Show what will be processed
        for csv_file in csv_files:
            self.stdout.write(f'  - {os.path.basename(csv_file)}')

        # Drop existing data if requested (only once at the beginning)
        if drop_existing and not dry_run:
            self.stdout.write(
                self.style.WARNING('\n🗑️  Dropping existing location data...')
            )
            self.drop_existing_data()
        
        # Drop specific states if requested
        if drop_states and not dry_run:
            self.stdout.write(
                self.style.WARNING(f'\n🗑️  Dropping data for states: {", ".join(drop_states)}...')
            )
            self.drop_specific_states(drop_states)

        # Initialize overall statistics
        overall_stats = {
            'files_processed': 0,
            'total_states': set(),
            'total_districts': set(),
            'total_subdistricts': set(),
            'total_villages': 0,
            'total_rows': 0
        }

        # Process each CSV file
        for i, csv_file in enumerate(csv_files, 1):
            self.stdout.write(
                self.style.SUCCESS(f'\n📁 Processing file {i}/{len(csv_files)}: {os.path.basename(csv_file)}')
            )
            
            try:
                file_stats = self.process_csv_file(csv_file, specific_state, dry_run)
                
                # Update overall statistics
                overall_stats['files_processed'] += 1
                overall_stats['total_states'].update(file_stats['states'])
                overall_stats['total_districts'].update(file_stats['districts'])
                overall_stats['total_subdistricts'].update(file_stats['subdistricts'])
                overall_stats['total_villages'] += file_stats['villages']
                overall_stats['total_rows'] += file_stats['rows_processed']
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error processing {csv_file}: {str(e)}')
                )
                continue

        # Show final summary
        self.show_final_summary(overall_stats, dry_run)

    def drop_existing_data(self):
        """Drop all existing location data"""
        self.stdout.write('Dropping existing location data...')
        
        with transaction.atomic():
            Village.objects.all().delete()
            SubDistrict.objects.all().delete()
            District.objects.all().delete()
            State.objects.all().delete()
            
        self.stdout.write(
            self.style.SUCCESS('Existing location data dropped successfully')
        )

    def drop_specific_states(self, states: List[str]):
        """Drop data for specific states"""
        self.stdout.write('Dropping data for specific states...')
        
        # Convert state names to title case for proper matching
        states_title_case = [state.title() for state in states]
        
        with transaction.atomic():
            Village.objects.filter(subdistrict__district__state__name__in=states_title_case).delete()
            SubDistrict.objects.filter(district__state__name__in=states_title_case).delete()
            District.objects.filter(state__name__in=states_title_case).delete()
            State.objects.filter(name__in=states_title_case).delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'Data for states: {", ".join(states)} dropped successfully')
        )

    def process_csv_file(self, csv_file: str, specific_state: Optional[str], dry_run: bool) -> Dict:
        """Process a single CSV file and return statistics"""
        stats = {
            'states': set(),
            'districts': set(),
            'subdistricts': set(),
            'villages': 0,
            'rows_processed': 0
        }

        # Define the correct field names based on the CSV structure
        correct_fieldnames = [
            'pc11_s_id', 'pc11_d_id', 'pc11_sd_id', 'pc11_tv_id',
            'state_name', 'district_n', 'subdistric', 'village_na',
            'place_name', 'tot_p', 'p_sc', 'p_st'
        ]

        with open(csv_file, 'r', encoding='utf-8') as file:
            # Skip the first line if it contains field definitions
            first_line = file.readline().strip()
            self.stdout.write(f'    🔍 First line: {first_line[:100]}...')
            
            if first_line.startswith('"pc11_s_id,C,'):
                # This is a field definition line, skip it
                self.stdout.write('    ✅ Skipping field definition line')
                reader = csv.DictReader(file, fieldnames=correct_fieldnames)
            else:
                # This is actual data, reset file pointer
                file.seek(0)
                self.stdout.write('    ⚠️  First line appears to be data, resetting file pointer')
                reader = csv.DictReader(file, fieldnames=correct_fieldnames)
            
            # Debug fieldnames
            self.stdout.write(f'    📋 Using fieldnames: {reader.fieldnames}')

            rows_to_process = []
            row_count = 0
            for row in reader:
                row_count += 1
                if row_count <= 3:  # Debug first few rows
                    self.stdout.write(f'    🔍 Row {row_count}: state="{row.get("state_name", "")}", district="{row.get("district_n", "")}", village="{row.get("village_na", "")}"')
                
                # Clean row data
                cleaned_row = {}
                for key, value in row.items():
                    cleaned_value = value.strip().strip('"') if value else value
                    cleaned_row[key] = cleaned_value
                
                # Debug state filtering
                if row_count <= 3:
                    state_in_row = cleaned_row.get('state_name', '')
                    self.stdout.write(f'    🏛️  State in row: "{state_in_row}" | Looking for: "{specific_state}"')
                
                # Filter by specific state if provided
                if specific_state and cleaned_row.get('state_name', '').lower() != specific_state.lower():
                    continue
                
                rows_to_process.append(cleaned_row)
                stats['rows_processed'] += 1

            self.stdout.write(f'    📊 Total rows in CSV: {row_count}, Rows matching filter: {len(rows_to_process)}')

            if dry_run:
                self.show_dry_run_stats(rows_to_process, stats)
                return stats

            # Process rows in batches for better performance
            self.process_rows_in_batches(rows_to_process, stats)

        self.show_processing_stats(stats)
        return stats

    def process_rows_in_batches(self, rows: List[Dict], stats: Dict):
        """Process rows in smaller batches with progress indicators"""
        batch_size = 250  # Reduced batch size for better performance
        total_batches = (len(rows) + batch_size - 1) // batch_size
        total_rows = len(rows)
        
        self.stdout.write(f'  📊 Processing {total_rows:,} rows in {total_batches} batches of {batch_size} rows each')
        
        start_time = time.time()
        
        for i in range(0, len(rows), batch_size):
            batch_start_time = time.time()
            batch = rows[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            rows_processed = min(i + batch_size, total_rows)
            
            # Progress indicator
            progress_percent = (rows_processed / total_rows) * 100
            self.stdout.write(
                f'  🔄 Batch {batch_num}/{total_batches} '
                f'({rows_processed:,}/{total_rows:,} rows - {progress_percent:.1f}%)'
            )
            
            try:
                with transaction.atomic():
                    for row_idx, row in enumerate(batch):
                        try:
                            self.process_single_row(row, stats)
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f'    ❌ Error in row {i + row_idx + 1}: {str(e)}')
                            )
                            # Continue processing other rows
                            continue
                
                # Calculate timing and ETA
                batch_time = time.time() - batch_start_time
                elapsed_time = time.time() - start_time
                avg_time_per_batch = elapsed_time / batch_num
                remaining_batches = total_batches - batch_num
                eta_seconds = remaining_batches * avg_time_per_batch
                
                # Show progress every 5 batches or at significant milestones
                if batch_num % 5 == 0 or batch_num == total_batches:
                    eta_str = f"{int(eta_seconds // 60)}m {int(eta_seconds % 60)}s" if eta_seconds > 0 else "Complete!"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'    ✅ Completed {rows_processed:,} rows ({progress_percent:.1f}%) | '
                            f'Batch: {batch_time:.1f}s | ETA: {eta_str}'
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'    ❌ Batch {batch_num} failed: {str(e)}')
                )
                # Continue with next batch
                continue
        
        total_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f'  ⏱️  Completed in {int(total_time // 60)}m {int(total_time % 60)}s')
        )

    def process_single_row(self, row: Dict, stats: Dict):
        """Process a single row from the CSV"""
        try:
            # Extract and validate data from row
            state_id = None
            district_id = None
            village_id = None  # Keep as string to preserve leading zeros
            
            try:
                state_id = int(row.get('pc11_s_id', 0)) if row.get('pc11_s_id') and row.get('pc11_s_id').strip() else None
                district_id = int(row.get('pc11_d_id', 0)) if row.get('pc11_d_id') and row.get('pc11_d_id').strip() else None
                # Keep village_id as string to preserve leading zeros (e.g., "037497")
                village_id = row.get('pc11_tv_id', '').strip() if row.get('pc11_tv_id') and row.get('pc11_tv_id').strip() else None
            except (ValueError, TypeError):
                # Skip rows with invalid ID format
                return
            
            subdistrict_id = row.get('pc11_sd_id', '').strip() if row.get('pc11_sd_id') else ''
            
            # Clean and validate names
            state_name = row.get('state_name', '').strip().title()
            district_name = row.get('district_n', '').strip().title()
            subdistrict_name = row.get('subdistric', '').strip().title()
            village_name = row.get('village_na', '').strip().title()
            
            # Skip rows with missing essential data
            if not all([state_name, district_name, subdistrict_name, village_name]):
                return
            
            # Population data with better error handling
            total_population = None
            sc_population = None
            st_population = None
            
            try:
                total_population = int(float(row.get('tot_p', 0))) if row.get('tot_p') and str(row.get('tot_p')).strip() else None
                sc_population = int(float(row.get('p_sc', 0))) if row.get('p_sc') and str(row.get('p_sc')).strip() else None
                st_population = int(float(row.get('p_st', 0))) if row.get('p_st') and str(row.get('p_st')).strip() else None
            except (ValueError, TypeError):
                # Use None for invalid population data
                pass

            # Create or get State
            state, created = State.objects.get_or_create(
                state_id=state_id,
                defaults={'name': state_name}
            )
            if created:
                stats['states'].add(state_name)

            # Create or get District
            district, created = District.objects.get_or_create(
                district_id=district_id,
                state=state,
                defaults={'name': district_name}
            )
            if created:
                stats['districts'].add(f"{district_name} ({state_name})")

            # Create or get SubDistrict
            subdistrict, created = SubDistrict.objects.get_or_create(
                subdistrict_id=subdistrict_id,
                district=district,
                defaults={'name': subdistrict_name}
            )
            if created:
                stats['subdistricts'].add(f"{subdistrict_name} ({district_name})")

            # Create or get Village with village_id as string to preserve leading zeros
            village, created = Village.objects.get_or_create(
                village_id=village_id,  # Now a string like "037497"
                subdistrict=subdistrict,
                defaults={
                    'name': village_name,
                    'total_population': total_population,
                    'sc_population': sc_population,
                    'st_population': st_population
                }
            )
            if created:
                stats['villages'] += 1
            elif not created and village.name != village_name:
                # Update village name if different (handle name variations)
                village.name = village_name
                village.save()

        except Exception as e:
            # More detailed error logging
            error_msg = f'Error processing row: {str(e)}'
            if 'state_name' in row:
                error_msg += f' | State: {row.get("state_name", "N/A")}'
            if 'village_na' in row:
                error_msg += f' | Village: {row.get("village_na", "N/A")}'
            
            self.stdout.write(self.style.ERROR(error_msg))

    def show_dry_run_stats(self, rows: List[Dict], stats: Dict):
        """Show statistics for dry run"""
        self.stdout.write(f'  Would process {len(rows)} rows')
        
        states = set()
        districts = set()
        subdistricts = set()
        villages = set()
        
        for row in rows:
            states.add(row.get('state_name', '').title())
            districts.add(row.get('district_n', '').title())
            subdistricts.add(row.get('subdistric', '').title())
            villages.add(row.get('village_na', '').title())
        
        self.stdout.write(f'  States: {len(states)}')
        self.stdout.write(f'  Districts: {len(districts)}')
        self.stdout.write(f'  SubDistricts: {len(subdistricts)}')
        self.stdout.write(f'  Villages: {len(villages)}')

    def show_processing_stats(self, stats: Dict):
        """Show processing statistics"""
        self.stdout.write(f'  New States: {len(stats["states"])}')
        self.stdout.write(f'  New Districts: {len(stats["districts"])}')
        self.stdout.write(f'  New SubDistricts: {len(stats["subdistricts"])}')
        self.stdout.write(f'  New Villages: {stats["villages"]}')
        self.stdout.write(f'  Total Rows: {stats["rows_processed"]}')

    def show_final_summary(self, overall_stats: Dict, dry_run: bool):
        """Show final processing summary"""
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('📊 DRY RUN SUMMARY - No data was actually inserted')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('📊 FINAL PROCESSING SUMMARY')
            )
        self.stdout.write('='*60)
        
        self.stdout.write(f'Files processed: {overall_stats["files_processed"]}')
        self.stdout.write(f'Total states: {len(overall_stats["total_states"])}')
        self.stdout.write(f'Total districts: {len(overall_stats["total_districts"])}')
        self.stdout.write(f'Total subdistricts: {len(overall_stats["total_subdistricts"])}')
        self.stdout.write(f'Total villages: {overall_stats["total_villages"]:,}')
        self.stdout.write(f'Total rows processed: {overall_stats["total_rows"]:,}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS('\n✅ Database population completed successfully!')
            )
        else:
            self.stdout.write(
                self.style.WARNING('\n💡 This was a dry run. Use without --dry-run to actually populate the database.')
            ) 