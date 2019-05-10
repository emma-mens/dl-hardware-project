# -*- coding: utf-8 -*-
from utility import write_yaml_file


file_path    = '1_8_1_1_2.yaml'
access_energy_table = {}
energy_table = {'idle': 0.24, 'RAM_access': access_energy_table}
#                   [nread, nwrite, nrepeated_read, n_repeated_data_write]
access_energy_table[(1,       0,       0,            0)] = 0.38 # read_only
access_energy_table[(0,       1,       0,            0)] = 1.0  # write_only
access_energy_table[(0,       0,       1,            0)] = 0.16 # read_repeat
access_energy_table[(1,       1,       0,            0)] = 1.34 # read_write
access_energy_table[(0,       1,       1,            0)] = 1.0  # read_repeat_write
access_energy_table[(1,       0,       0,            1)] = 0.85 # read_only_write_repeated_data
access_energy_table[(0,       0,       1,            1)] = 0.5  # read_repeat_write_repeated_data
access_energy_table[(0,       0,       0,            1)] = 0.5  # write_repeated_data
write_yaml_file(file_path, energy_table)

# ============================================================================
#  Ignore write repeat data attributes
# ============================================================================
#access_energy_table[(1,       0,       0,            0)] = 0.38 # read_only
#access_energy_table[(0,       1,       0,            0)] = 1.0  # write_only
#access_energy_table[(0,       0,       1,            0)] = 0.16 # read_repeat
#access_energy_table[(1,       1,       0,            0)] = 1.34 # read_write
#access_energy_table[(0,       1,       1,            0)] = 1.0  # read_repeat_write
#access_energy_table[(1,       0,       0,            1)] = 0.34 # read_only_write_repeated_data
#access_energy_table[(0,       0,       1,            1)] = 1.0  # read_repeat_write_repeated_data
#access_energy_table[(0,       0,       0,            1)] = 1.0  # write_repeated_data
#write_yaml_file(file_path, energy_table)


#access_energy_table[(1,       0,       0,            0)] = 0.38  # read_only
#access_energy_table[(0,       1,       0,            0)] = 1.0   # write_only
#access_energy_table[(0,       0,       1,            0)] = 0.16  # read_repeat
#access_energy_table[(1,       1,       0,            0)] = 1.34  # read_write
#access_energy_table[(0,       1,       1,            0)] = 1.16  # read_repeat_write
#access_energy_table[(1,       0,       0,            1)] = 1.34  # read_only_write_repeated_data
#access_energy_table[(0,       0,       1,            1)] = 1.16  # read_repeat_write_repeated_data
#access_energy_table[(0,       0,       0,            1)] = 1.0   # write_repeated_data
#write_yaml_file(file_path, energy_table)



file_path    = '224_16_1_1_2.yaml'
access_energy_table = {}
energy_table = {'idle': 0.55, 'RAM_access': access_energy_table}
#                   [nread, nwrite, nrepeated_read, n_repeated_data_write]
access_energy_table[(1,       0,       0,            0)] = 4.53  # read_only
access_energy_table[(0,       1,       0,            0)] = 5.45  # write_only
access_energy_table[(0,       0,       1,            0)] = 4.41  # read_repeat
access_energy_table[(1,       1,       0,            0)] = 9.65  # read_write
access_energy_table[(0,       1,       1,            0)] = 5.45  # read_repeat_write
access_energy_table[(1,       0,       0,            1)] = 9.65  # read_only_write_repeated_data
access_energy_table[(0,       0,       1,            1)] = 5.45  # read_repeat_write_repeated_data
access_energy_table[(0,       0,       0,            1)] = 5.45  # write_repeated_data
write_yaml_file(file_path, energy_table)


file_path    = '224_16_1_1_2.yaml'
access_energy_table = {}
energy_table = {'idle': 0.55, 'RAM_access': access_energy_table}
#                   [nread, nwrite, nrepeated_read, n_repeated_data_write]
access_energy_table[(1,       0,       0,            0)] = 4.53  # read_only
access_energy_table[(0,       1,       0,            0)] = 5.45  # write_only
access_energy_table[(0,       0,       1,            0)] = 4.41  # read_repeat
access_energy_table[(1,       1,       0,            0)] = 9.65  # read_write
access_energy_table[(0,       1,       1,            0)] = 5.45  # read_repeat_write
access_energy_table[(1,       0,       0,            1)] = 9.65  # read_only_write_repeated_data
access_energy_table[(0,       0,       1,            1)] = 5.45  # read_repeat_write_repeated_data
access_energy_table[(0,       0,       0,            1)] = 5.45  # write_repeated_data
write_yaml_file(file_path, energy_table)




file_path    = '1024_16_4_2_2.yaml'
access_energy_table = {}
energy_table = {'idle': 1.2 , 'RAM_access': access_energy_table}
#                   [nread, nwrite, nrepeated_read, n_repeated_data_write]
access_energy_table[(1,       0,       0,            0)] = 22.3 # read_only
access_energy_table[(0,       1,       0,            0)] = 40.2  # write_only
access_energy_table[(0,       0,       1,            0)] = 22.3 # read_repeat
access_energy_table[(1,       1,       0,            0)] = 62.5 # read_write
access_energy_table[(0,       1,       1,            0)] = 40.2  # read_repeat_write
access_energy_table[(1,       0,       0,            1)] = 62.5 # read_only_write_repeated_data
access_energy_table[(0,       0,       1,            1)] = 62.5 # read_repeat_write_repeated_data
access_energy_table[(0,       0,       0,            1)] = 40.2 # write_repeated_data
write_yaml_file(file_path, energy_table)