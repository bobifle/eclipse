import glob
import subprocess

if __name__ == '__main__':
	pyf = glob.glob("**/*.py")
	for f in pyf:
		subprocess.call(['pylint', f, '--rcfile', 'test/.pylintrc'])
