import os, sys, xxhash, random, time
import secp256k1
from pybloomfilter import BloomFilter
from sys import argv
from multiprocessing import Process, cpu_count, Value, Event

# Color class for terminal output
class color:
    GREEN = '\033[32m'
    RED = '\033[31m'
    X = '\033[5m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Splash screen
bsplash = '''
█▀▄ █░░ ▄▀▄ ▄▀▄ █▄░▄█     █▀ ▀ █░░ ▀█▀ █▀▀ █▀▀▄ 
█▀█ █░▄ █░█ █░█ █░█░█     █▀ █ █░▄ ░█░ █▀▀ █▐█▀ 
▀▀░ ▀▀▀ ░▀░ ░▀░ ▀░░░▀     ▀░ ▀ ▀▀▀ ░▀░ ▀▀▀ ▀░▀▀ 
'''

# Parse input arguments
target_pubkey_hex = argv[1]  # First argument is now a hex string (public key)
bloom_filter_name = argv[2]  # Second argument is the bloom filter name
filebase = argv[3]           # Third argument is the base name for output files
bit = int(argv[4])           # Fourth argument is the bit size
core = int(argv[5])          # Fifth argument is the number of CPU cores

# Print program info
def pr():
    os.system('cls||clear')
    print(color.GREEN + bsplash + color.END)
    print(color.RED + 'by pianist (Telegram: @pianist_coder | btc: bc1q0jth0rjaj2vqtqgw45n39fg4qrjc37hcw4frcz)' + color.END)
    print(color.BOLD + '\n[+] Program started' + color.END)
    print("-"*87)
    print(f'[+] Public Key: {target_pubkey_hex}')
    print(f'[+] Bloom Filter: {bloom_filter_name}')
    print(f'[+] Bit Size: {bit}')
    print(f'[+] Cores: {core}')
    print("-"*87)

# Initialize the Bloom Filter
count = 10000  # Default value for demonstration
if os.path.exists(bloom_filter_name):
    bf = BloomFilter.open(bloom_filter_name)
else:
    bf = BloomFilter(count, 0.0000000001, bloom_filter_name)

st = time.time()

# Function to generate random private keys and public keys
def generate_random_bloom(start, end):
    rnd = {}
    for _ in range(10000):
        x = random.randint(2 ** start - (2 ** start - 5), 2 ** end - 1)
        priv_key = secp256k1.PrivateKey(x.to_bytes(32, byteorder='big'))  # Private key
        pub_key = priv_key.pubkey.serialize()  # Public key in compressed format
        rnd[pub_key] = f'{x:x}'  # Map public key to private key
    return rnd

# Display formatted numbers (e.g., K for thousand, M for million)
def scan_str(num):
    suffixes = ["", "K", "M", "B", "T"]
    exponent = 0
    while abs(num) >= 1000 and exponent < 4:
        num /= 1000
        exponent += 1
    return f"{num:.2f} {suffixes[exponent]}"

# Display time in hours, minutes, and seconds
def display_time(seconds):
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{seconds:05.2f}"

# Calculate and display key generation speed
def speedup(st, counter):
    speed = counter / (time.time() - st)
    print(f'[{scan_str(counter)}] [{scan_str(speed)}keys] [{display_time(time.time() - st)}]      ', end = '\r')

# Start parallel key generation and Bloom filter scanning
def bloom_start(cores='all'):
    try:
        available_cores = cpu_count()
        if cores == 'all': cores = available_cores
        elif 0 < int(cores) <= available_cores: cores = int(cores)
        else: cores = 1
        counter = Value('L')  # Shared counter for processes
        workers = []
        match = Event()  # Event to signal completion
        for r in range(cores):
            p = Process(target=bloom_create, args=(counter, r, match))
            workers.append(p)
            p.start()
        for worker in workers:
            worker.join()
    except (KeyboardInterrupt, SystemExit):
        exit('\nSIGINT or CTRL-C detected. Exiting gracefully. BYE')
    sys.stdout.write('\n\n[+] Bloom creating complete in {0:.2f} sec\n'.format(time.time() - st))

# Save generated key data to file and add to Bloom filter
def save_data(data, filename):
    with open(filename, "a") as f:
        for item, value in data.items():
            f.write(f'{value};{xxhash.xxh64(item).hexdigest()}\n')
            bf.add(item)

# Generate keys, save to file, and update the Bloom filter
def bloom_create(counter, r, match):
    st = time.time()
    while not match.is_set():
        if match.is_set(): return
        temp = generate_random_bloom(bit - 1, bit)  # Generate random keys in the given range
        save_data(temp, filebase)
        with counter.get_lock(): counter.value += 10000  # Update counter
        if counter.value % 1000000 == 0:
            speedup(st, counter.value)
        if counter.value >= count - (core - 1) * 10000:
            match.set()  # Set event to stop the process

# Run the program
pr()
bloom_start(cores=core)

