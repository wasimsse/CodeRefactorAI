def calculate_total(items):
    total = 0
    for item in items:
        total = total + item
    return total

def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
        else:
            result.append(0)
    return result

def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j]:
                duplicates.append(arr[i])
    return duplicates

def main():
    numbers = [1, 2, 3, 4, 5]
    total = calculate_total(numbers)
    processed = process_data(numbers)
    duplicates = find_duplicates([1, 2, 2, 3, 3, 4])
    
    print(f"Total: {total}")
    print(f"Processed: {processed}")
    print(f"Duplicates: {duplicates}")

if __name__ == "__main__":
    main() 