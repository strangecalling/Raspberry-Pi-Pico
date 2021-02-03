
# Pi Pico used for 3D printer enclosure heater control
# AHT10 temp/humdity wired to I2C 0 on pins 12 and 13
# On-board switch (TP6) wired to GP4 to allow function select and reset
# On-board switch (GPIO25) used for mode indication, temperature, timer complete and thermal runaway error.
# GPIO to be selected for 3.3V relay control of a 240V PTC heater element and 12V Fan
# Thermal runaway detection and heater timer.
# Mode number is flashed on selection 
# Default mode (1) is heater off, also it flashes the temperature, eg. 22 degrees C, slow flash twice (10's), fast flash twice (1's).
# Mode number also flashed.
# Mode 2 is set to 50 degrees C with 320 minutes timer (ABS prints)
# Mode 3 is set to 30 with 30 minutes timer (printer pre heat for cold or humid conditions)
# The onboard LED is on while heating in Modes 2 and 3.
# It also displays status for these modes continous flashing means timer is complete,
# Fast flashing indicates the thermal runaway has detected a fault.
# Press onboard switch for 1 second to reset the timer or fault and start heater. Thermal runaway pauses the timer.
# Reselecting a mode resets both timer and fault.

from machine import Pin, I2C, ADC
from utime import sleep, ticks_ms

led = Pin(25, machine.Pin.OUT)         # onboard_LED
switch = Pin(4, machine.Pin.IN)        # onboard_switch wired TP6 wired to GP4
i2c = I2C(0, scl=Pin(13), sda=Pin(12)) # AHT10 connected to pins 16 (SDA), 17 (SCL), 18 (Gnd) and 36 (3V3) 
onboard_temp = ADC(4)
count = 1
cycle_time = 5
previous_temp = 0
runaway_flag = 0
timer_reached = 0
minute_counter = 0

def get_temp():
    raw_temp = onboard_temp.read_u16() * 3.3 / (65535)
    temperature = - (raw_temp * 589.06) + 444.88   # Calibrated to AHT10 sensor
    return temperature

def num_formatted(num, places):
    num_formatted = round(num*(10^places))/(10^places)
    return num_formatted

def get_temp_and_humidity():
    # AHT10 temp/humidity sensor
    i2c.writeto(0x38, b'\xE1\x08\x00')   # config device
    sleep(0.1)
    i2c.writeto(0x38, b'\xAC\x33\x00')   # send measure command
    sleep(0.5)
    data = i2c.readfrom(0x38, 32)    # Read Data
    temp_raw = ((data[3] & 0x0F) << 16)|(data[4] <<8)|data[5]
    temp = ((temp_raw*194.54)/1048576)-49.91
    temp_formatted = num_formatted(temp, 2)
    hum_raw = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    hum = int(hum_raw * 100 / 1048576)
    return temp_formatted, hum, temp_raw, hum_raw

def heater(set_temp, timeM = 10):
    global previous_temp, runaway_flag, timer_reached, minute_counter
    if minute_counter >= timeM:
        heateroff()
        timer_reached = 1
        print('Timer Complete, power cycle or select a different mode to restart heater control.')
        minute_counter = 0
    else:
        data = get_temp_and_humidity()
        temp = data[0]
        if set_temp > temp:
            if previous_temp >= temp:
                heateroff()
                print('Thermal runaway detected, power cycle or select a different mode.')
                runaway_flag = 1
                previous_temp = 0
                timer_Reached = 0
            else:
                heateron()
                print('Heater ON, target temp',set_temp,'. Actual temp',temp,'.')
                previous_temp = temp
        else:
            heateroff()
            print('Heater OFF, target temp',set_temp,'is reached. Actual temp',temp,'.')
            previous_temp = 0
        if runaway_flag != 1 or timer_reached == 1:
            minute_counter = minute_counter + 1
            sleep(60)
            #sleep(5)        #test

def heateron():
    # gpio to be assigned
    led_on()    # Indication only

def heateroff():
    # gpio to be assigned
    led_off     # Indication only
    
def led_off():
    led.value(0)

def led_on():
    led.value(1)
    
def led_flash():
    led.toggle()
        
def led_flash_num_adjustable(num, cycleT = 0.5):
    count = 0
    while count < num:
        count = count + 1
        led_on()
        sleep(cycleT/2)
        led_off()
        sleep(cycleT/2)
        
def flash_hundreds_tens_ones(arg, onesT = 0.3, tensT = 0.6, hundredsT = 1.8):
    hundreds = int(arg/100)
    tens = int(arg/10 - (hundreds*10))
    ones = int(arg-tens*10-hundreds*100)
    if hundreds > 0:
        #print("Flash Hundreds (",hundreds,")")     # test only
        led_flash_num_adjustable(hundreds, hundredsT)
    if tens > 0:
        #print("Flash Tens (",tens,")")             # test only
        led_flash_num_adjustable(tens, tensT)
        sleep(hundredsT-tensT)
    if ones > 0 :
        #print("Flash Ones (",ones,")")            # test only
        led_flash_num_adjustable(ones , onesT)
        sleep(hundredsT-tensT-onesT)
    
def flash_temp_and_humidity():
    temp_onboard = get_temp()                    # onboard temp
    data = get_temp_and_humidity()               # AHT10 sensor
    print("Onboard Temp is",temp_onboard,"I2C temp is",data[0],"I2C humidity is",data[1])
    #print("Raw temp is",data[2],"Raw Humidity is",data[3])        # test only, used for calibration
    flash_hundreds_tens_ones(data[0])

def cycle_timer():
    new_time = ticks_ms()
    time_diff= new_time - old_time
    old_time = new_time
    print(time_diff)

def intro():
    print("LED intro")
    led_off()
    led_flash_num_adjustable(20, cycleT = 0.2)
    led_off()
    sleep(1)

intro()             # Flashes LED on initial start
led_off()
old_time = ticks_ms()  # used for testing to check time to run code; used with cycle_timer() function
time_diff = 0          # as above
mode_num = 1           # default mode

while False:
    test = script     # test only
    
while True: # Runs whichever mode is selected
    switchval = switch.value()
    while switchval:
        if mode_num == 1:
            # Default - Heater cotrols off
            # Heater Off
            print("Mode 1: Heater OFF")
            led_flash_num_adjustable(1, 0.1)
            sleep(2)
            flash_temp_and_humidity()
        elif mode_num == 2:
            # Temp control 50 degrees C
            # Heater control at 50
            if runaway_flag == 1:
                led_flash_num_adjustable(10, 0.1)
            else:
                if timer_reached == 1:
                    led_flash_num_adjustable(2, 0.5)
                else:
                    print("Mode 2: Heater on 50")
                    heater(50, 320)   # set temp and timer in minutes
                    #heater(25, 5)     # test
                
        elif mode_num == 3:
            # setting 2 temp control 30 degrees C
            # Heater Control at 30
            if runaway_flag == 1:
                led_flash_num_adjustable(10, 0.1)
            else:
                if timer_reached == 1:
                    led_flash_num_adjustable(2, 0.5)
                else:
                    print("Mode 2: Heater on 30")
                    heater(30, 30)
                    #heater(25, 5)   #test
        switchval = switch.value()
    else:   # Mode select or reset active
        if runaway_flag == 1 or timer_reached == 1:
            if runaway_flag == 1:
                print('Heater control error reset')
                print('Timer still active, reset by power cycling or reselecting the mode')
                
            print("Mode still set to:",mode_num)
        
        else:  
            if mode_num >= 3:
                mode_num = 1
            else:
                mode_num = mode_num + 1
            print("Mode Changed :",mode_num)
        sleep(1)
        led_flash_num_adjustable(mode_num, 0.5)
        runaway_flag = 0
        timer_reached = 0
        sleep(2)
        switchval = switch.value()   
