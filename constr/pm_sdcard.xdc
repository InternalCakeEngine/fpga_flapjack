# From scratch constrinsts for the SD card pmod

# We have 12 pins on the module...
#  1	~CS	Chip Select / Data3	   SIGNAL
#  2	MOSI	MOSI / Command     SIGNAL
#  3	MISO	MISO / Data0       SIGNAL
#  4	SCK	Serial Clock           SIGNAL
#  5	GND	Power Supply Ground
#  6	VCC	Power Supply (3.3V)
#  7	DAT1	Data 1             SIGNAL (later)
#  8	DAT2	Data 2             SIGNAL (later)
#  9	CD	Card Detect            SIGNAL
# 10	WP	Write Protect          SIGNAL
# 11	GND	Power Supply Ground
# 12	VCC	Power Supply (3.3V)

# From the Arty7 reference manual:
#           JA      JB      JC     JD
# Pmod Type Std     HighSp  HighSp  Std
# Pin 1	    G13	    E15	    U12	    D4
# Pin 2	    B11	    E16	    V12	    D3
# Pin 3	    A11	    D15	    V10	    F4
# Pin 4	    D12	    C15	    V11	    F3
# Pin 7	    D13	    J17	    U14	    E2
# Pin 8	    B18	    J18	    V14	    D2
# Pin 9     A18	    K15	    T13	    H2
# Pin 10    K16	    J15	    U13	    G2

set_property -dict {PACKAGE_PIN G13 IOSTANDARD LVCMOS33} [get_ports {sd_cs}];
set_property -dict {PACKAGE_PIN B11 IOSTANDARD LVCMOS33} [get_ports {sd_mosi}];
set_property -dict {PACKAGE_PIN A11 IOSTANDARD LVCMOS33} [get_ports {sd_miso}];
set_property -dict {PACKAGE_PIN D12 IOSTANDARD LVCMOS33} [get_ports {sd_clk}];
set_property -dict {PACKAGE_PIN A18 IOSTANDARD LVCMOS33} [get_ports {sd_cd}];
set_property -dict {PACKAGE_PIN K16 IOSTANDARD LVCMOS33} [get_ports {sd_wp}];
