import os
import datetime
from dc24_ingester_platform.utils import *

def process(cwd, data_entries):
    ret = []
    arg_list = [param.strip() for param in "{args}".split(',')]

    tree_file_field = "{file_field}"
    sensor_temp_field = "{temp_field}"
    sensor_humidity_field = "{humidity_field}"
    temp_sensor_id = "{temp_sensor_id}"
    humidity_sensor_id = "{humidity_sensor_id}"

    parsing_temp = False
    parsing_humidity = False
    for data_entry in data_entries:
        with open(os.path.join(cwd, data_entry[tree_file_field].f_path)) as f:
            for l in f.readlines():
                l = l.strip()
				if l == "BEGIN TEMP": parsing_temp = True
                elif l == "END TEMP": parsing_temp = False
				elif l == "BEGIN HUMIDITY": parsing_humidity = True
                elif l == "END HUMIDITY": parsing_humidity = False
                else:
                    # parse line
					new_data_entry = None
                    l = l.split(",")
					if parsing_temp:
						if len(l) != 3: continue
						if l[1] != temp_sensor_id: continue
						if new_data_entry is None:						
							new_data_entry = DataEntry(timestamp=datetime.datetime.now())
						new_data_entry[sensor_temp_field] = float(l[2])
						
					elif parsing_humidity:
						if len(l) != 5: continue
						if l[1] != humidity_sensor_id: continue
						if new_data_entry is None:						
							new_data_entry = DataEntry(timestamp=datetime.datetime.now())
						new_data_entry[sensor_humidity_field] = calculate_humidity(float(l[2]), float(l[3]), float(l[4]))
					
					if new_data_entry is not None:
						ret.append( new_data_entry )
						
    return ret
	
def calculate_humidity(temp, Vs, Vo):
    d = 0.1515
    c = 0.00636

    e = 1.0546
    f = 0.00216

    sensor_rh = ((Vo / Vs) - d) / c
    true_rh = sensor_rh / (e - (f * temp))
    return true_rh
