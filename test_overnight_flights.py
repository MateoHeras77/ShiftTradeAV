#!/usr/bin/env python3
"""
Test script to validate overnight flight calendar generation
"""

import sys
import os
import datetime as dt
from datetime import datetime, date

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit secrets for testing
class MockSecrets:
    def __getitem__(self, key):
        # Return appropriate dummy values for testing
        if key == "SMTP_PORT":
            return "587"
        elif key in ["SUPABASE_URL", "SUPABASE_KEY"]:
            return "https://test.supabase.co" if key == "SUPABASE_URL" else "test_key"
        else:
            return "test_value"

# Mock streamlit module
class MockStreamlit:
    secrets = MockSecrets()
    
    def error(self, msg):
        print(f"ST ERROR: {msg}")

# Replace streamlit import for testing
sys.modules['streamlit'] = MockStreamlit()

import types
supabase_dummy = types.SimpleNamespace(create_client=lambda *args, **kwargs: None, Client=object)
sys.modules['supabase'] = supabase_dummy

# Provide a minimal pytz replacement for tests
class DummyTZ(dt.tzinfo):
    def __init__(self, offset_hours=0):
        self.offset = dt.timedelta(hours=offset_hours)
    def utcoffset(self, _dt):
        return self.offset
    def dst(self, _dt):
        return dt.timedelta(0)
    def tzname(self, _dt):
        return 'UTC'
    def localize(self, value):
        return value.replace(tzinfo=self)

def timezone(_name):
    # Simplified: return UTC for any timezone
    return DummyTZ()

pytz_dummy = types.SimpleNamespace(timezone=timezone, UTC=DummyTZ())
sys.modules['pytz'] = pytz_dummy

from shifttrade import utils

def test_overnight_flights():
    """Test overnight flight calendar generation"""
    print("Testing overnight flight calendar generation...")
    
    # Test data for AV205 (overnight flight)
    test_shift_data_av205 = {
        'id': 'test_123',
        'flight_number': 'AV205',
        'date_request': '2025-06-01',  # June 1st, 2025
        'requester_name': 'Juan Pérez',
        'cover_name': 'María García',
        'supervisor_name': 'Carlos Supervisor'
    }
    
    # Test data for AV625 (overnight flight)
    test_shift_data_av625 = {
        'id': 'test_456',
        'flight_number': 'AV625',
        'date_request': '2025-06-02',  # June 2nd, 2025
        'requester_name': 'Ana López',
        'cover_name': 'Pedro Martín',
        'supervisor_name': 'Laura Supervisor'
    }
    
    # Test data for AV255 (regular daytime flight for comparison)
    test_shift_data_av255 = {
        'id': 'test_789',
        'flight_number': 'AV255',
        'date_request': '2025-06-03',  # June 3rd, 2025
        'requester_name': 'Roberto Silva',
        'cover_name': 'Carmen Torres',
        'supervisor_name': 'Miguel Supervisor'
    }

    # Test data for AV627-AV205 (combo overnight)
    test_shift_data_combo = {
        'id': 'test_999',
        'flight_number': 'AV627-AV205',
        'date_request': '2025-06-04',  # June 4th, 2025
        'requester_name': 'Luis Gómez',
        'cover_name': 'Mario Díaz',
        'supervisor_name': 'Julia Supervisor'
    }
    
    print("\n1. Testing flight schedule info function:")
    
    # Test get_flight_schedule_info function
    schedule_av205 = utils.get_flight_schedule_info('AV205')
    schedule_av625 = utils.get_flight_schedule_info('AV625')
    schedule_av255 = utils.get_flight_schedule_info('AV255')
    schedule_combo1 = utils.get_flight_schedule_info('AV255-AV627')
    schedule_combo2 = utils.get_flight_schedule_info('AV619-AV627')
    schedule_combo3 = utils.get_flight_schedule_info('AV627-AV205')
    
    print(f"AV205 schedule: {schedule_av205}")
    print(f"AV625 schedule: {schedule_av625}")
    print(f"AV255 schedule: {schedule_av255}")
    
    # Validate overnight flags
    assert schedule_av205['is_overnight'] == True, "AV205 should be overnight"
    assert schedule_av625['is_overnight'] == True, "AV625 should be overnight"
    assert schedule_av255['is_overnight'] == False, "AV255 should not be overnight"
    assert schedule_combo1['is_overnight'] == False, "AV255-AV627 should not be overnight"
    assert schedule_combo2['is_overnight'] == False, "AV619-AV627 should not be overnight"
    assert schedule_combo3['is_overnight'] == True, "AV627-AV205 should be overnight"
    
    print("✅ Flight schedule info tests passed!")
    
    print("\n2. Testing calendar file generation:")
    
    # Test calendar file generation for AV205
    try:
        calendar_content_av205 = utils.create_calendar_file(test_shift_data_av205, is_for_requester=False)
        if calendar_content_av205:
            print("✅ AV205 calendar file generated successfully")
            
            # Check if the calendar contains the correct UTC times
            # AV205: 20:00 Toronto (June 1) = 00:00 UTC (June 2)
            # AV205: 00:30 Toronto (June 2) = 04:30 UTC (June 2)
            if "20250602T000000Z" in calendar_content_av205 and "20250602T043000Z" in calendar_content_av205:
                print("✅ AV205 calendar correctly shows UTC times for overnight flight")
            else:
                print("❌ AV205 calendar may not handle overnight transition correctly")
                
        else:
            print("❌ Failed to generate AV205 calendar")
    except Exception as e:
        print(f"❌ Error generating AV205 calendar: {e}")
    
    # Test calendar file generation for AV625
    try:
        calendar_content_av625 = utils.create_calendar_file(test_shift_data_av625, is_for_requester=False)
        if calendar_content_av625:
            print("✅ AV625 calendar file generated successfully")
            
            # Check if the calendar contains the correct UTC times
            # AV625: 20:00 Toronto (June 2) = 00:00 UTC (June 3)
            # AV625: 02:30 Toronto (June 3) = 06:30 UTC (June 3)
            if "20250603T000000Z" in calendar_content_av625 and "20250603T063000Z" in calendar_content_av625:
                print("✅ AV625 calendar correctly shows UTC times for overnight flight")
            else:
                print("❌ AV625 calendar may not handle overnight transition correctly")
                
        else:
            print("❌ Failed to generate AV625 calendar")
    except Exception as e:
        print(f"❌ Error generating AV625 calendar: {e}")

    # Test calendar file generation for AV627-AV205 (combo)
    try:
        calendar_content_combo = utils.create_calendar_file(test_shift_data_combo, is_for_requester=False)
        if calendar_content_combo:
            print("✅ AV627-AV205 calendar file generated successfully")

            # Check if the calendar contains the correct UTC times
            # Start: 13:00 Toronto (June 4) = 17:00 UTC (June 4)
            # End: 00:30 Toronto (June 5) = 04:30 UTC (June 5)
            if "20250604T170000Z" in calendar_content_combo and "20250605T043000Z" in calendar_content_combo:
                print("✅ AV627-AV205 calendar correctly shows UTC times for overnight combo")
            else:
                print("❌ AV627-AV205 calendar may not handle overnight transition correctly")

        else:
            print("❌ Failed to generate AV627-AV205 calendar")
    except Exception as e:
        print(f"❌ Error generating AV627-AV205 calendar: {e}")

    # Test calendar file generation for AV255 (regular flight)
    try:
        calendar_content_av255 = utils.create_calendar_file(test_shift_data_av255, is_for_requester=False)
        if calendar_content_av255:
            print("✅ AV255 calendar file generated successfully")
            
            # Check if the calendar contains the correct UTC times
            # AV255: 05:00 Toronto (June 3) = 09:00 UTC (June 3)
            # AV255: 10:00 Toronto (June 3) = 14:00 UTC (June 3)
            if "20250603T090000Z" in calendar_content_av255 and "20250603T140000Z" in calendar_content_av255:
                print("✅ AV255 calendar correctly shows UTC times for daytime flight")
            else:
                print("❌ AV255 calendar may have incorrect times")
                
        else:
            print("❌ Failed to generate AV255 calendar")
    except Exception as e:
        print(f"❌ Error generating AV255 calendar: {e}")
    
    print("\n3. Testing calendar content details:")
    
    # Print sample calendar content for review
    if 'calendar_content_av205' in locals():
        print("\nSample AV205 calendar content (first 500 chars):")
        print(calendar_content_av205[:500] + "...")
        
        # Check for proper flight schedule display in description
        if "20:00-00:30 (día siguiente)" in calendar_content_av205:
            print("✅ AV205 calendar includes correct schedule display")
        else:
            print("❌ AV205 calendar missing proper schedule display")

    if 'calendar_content_combo' in locals():
        if "13:00-00:30 (día siguiente)" in calendar_content_combo:
            print("✅ AV627-AV205 calendar includes correct schedule display")
        else:
            print("❌ AV627-AV205 calendar missing proper schedule display")
    
    print("\n4. Detailed calendar analysis:")
    
    # Let's print the full calendar content to debug
    if 'calendar_content_av205' in locals():
        print("\nFull AV205 calendar content:")
        print(calendar_content_av205)
        print("\n" + "="*50)
    
    if 'calendar_content_av625' in locals():
        print("\nFull AV625 calendar content:")
        print(calendar_content_av625)
        print("\n" + "="*50)
    
    if 'calendar_content_av255' in locals():
        print("\nFull AV255 calendar content:")
        print(calendar_content_av255)
        print("\n" + "="*50)

    if 'calendar_content_combo' in locals():
        print("\nFull AV627-AV205 calendar content:")
        print(calendar_content_combo)
        print("\n" + "="*50)

    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_overnight_flights()
