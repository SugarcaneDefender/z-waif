from utils import zw_logging
import os
import time
import traceback

def test_basic_logging():
    print("\n=== Testing Basic Logging ===")
    zw_logging.log_info("Test info message")
    zw_logging.log_error("Test error message")
    print("Basic logging test completed")

def test_message_length():
    print("\n=== Testing Message Length Warnings ===")
    # Test short message
    zw_logging.log_message_length_warning("short", 5, "test")
    # Test long message
    zw_logging.log_message_length_warning("x" * 2500, 2500, "test")
    print("Message length test completed")

def test_stream_status():
    print("\n=== Testing Stream Status ===")
    zw_logging.log_stream_status(True)
    zw_logging.log_stream_status(False)
    print("Stream status test completed")

def test_error_handling():
    print("\n=== Testing Error Handling ===")
    try:
        raise ValueError("Test error with traceback")
    except Exception as e:
        zw_logging.log_error(f"Caught error: {str(e)}")
    print("Error handling test completed")

def test_log_rotation():
    print("\n=== Testing Log Rotation ===")
    # Write enough messages to potentially trigger rotation
    for i in range(100):
        zw_logging.log_info(f"Test message {i} for rotation testing")
    print("Log rotation test completed")

def test_rag_log():
    print("\n=== Testing RAG Log ===")
    zw_logging.update_rag_log("Test RAG log entry")
    zw_logging.clear_rag_log()
    print("RAG log test completed")

def test_kelvin_log():
    print("\n=== Testing Kelvin Log ===")
    zw_logging.update_kelvin_log("Test Kelvin temperature: 0.7")
    print("Kelvin log test completed")

def verify_log_file():
    print("\n=== Verifying Log File ===")
    log_path = os.path.join(zw_logging.LOGS_DIR, "app.log")
    print(f"Log file path: {log_path}")
    print(f"Log file exists: {os.path.exists(log_path)}")
    
    if os.path.exists(log_path):
        print("\nLast 10 lines of log file:")
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print("".join(lines[-10:]))
        
        # Check for backup files
        backup_files = [f for f in os.listdir(zw_logging.LOGS_DIR) if f.startswith("app.log.")]
        if backup_files:
            print(f"\nFound {len(backup_files)} backup files:")
            for backup in backup_files:
                print(f"- {backup}")

def main():
    print("Starting comprehensive logging system test...")
    print(f"Log directory: {zw_logging.LOGS_DIR}")
    
    # Run all tests
    test_basic_logging()
    test_message_length()
    test_stream_status()
    test_error_handling()
    test_log_rotation()
    test_rag_log()
    test_kelvin_log()
    
    # Verify results
    verify_log_file()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main() 