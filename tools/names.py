import json

def main():
	with open('data/names.txt', 'r') as fname:
		with open('data/names.json', 'w') as jfile:
			jfile.write(json.dumps({"male":filter(bool, fname.read().split('\n'))}))

if __name__ == '__main__':
	main()
