from collections import deque
import random
import time

buffer_size = 10
buffer = deque(maxlen=buffer_size)

while True:
    # Generate a random integer and append it to the buffer
    random_int = random.randint(1, 100)  # Adjust range as needed
    buffer.append(random_int)
    
    # Introduce a short delay
    time.sleep(0.5)  # Adjust delay time as needed
    
    # Get the number of values currently in the buffer
    num_values = len(buffer)
    
    print("Buffer:", list(buffer))  # Optional: Print the buffer to see the values
    print("Number of values in the buffer:", num_values)
