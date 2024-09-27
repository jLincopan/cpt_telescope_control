import time

# Define theinitial value and print it
value = "Initial value"
print(value)# Print without adding a new line
print(value)

time.sleep(1)  # Wait for a second to simulate the change

# Change the value and overwrite the previous line
value = "Changed value"
print(value, end="\r\r") # Overwrite the previous line
print("")
