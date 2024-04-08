import threading
import time

class MyThreadedClass:
    def __init__(self):
        self.shutdown_event = threading.Event()  # Event to signal shutdown
        self.input_thread = threading.Thread(target=self.input_func)

    def thread_func_1(self):
        while not self.shutdown_event.is_set():
            print("Thread 1 is running...")
            time.sleep(10)

    def thread_func_2(self):
        while not self.shutdown_event.is_set():
            print("Thread 2 is running...")
            time.sleep(10)

    def input_func(self):
        while not self.shutdown_event.is_set():
            user_input = input("Enter a command: ")
            if user_input.lower() == "exit":
                self.shutdown()
                break

    def start(self):
        self.thread_1 = threading.Thread(target=self.thread_func_1)
        self.thread_2 = threading.Thread(target=self.thread_func_2)

        self.thread_1.start()
        self.thread_2.start()
        self.input_thread.start()

    def shutdown(self):
        # Set the shutdown event to signal threads to stop
        self.shutdown_event.set()
        # Wait for all threads to finish
        if self.thread_1.is_alive():
            self.thread_1.join()
        if self.thread_2.is_alive():
            self.thread_2.join()

# Usage example:
my_instance = MyThreadedClass()
my_instance.start()
