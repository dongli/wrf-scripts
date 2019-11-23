import cli

def has_key(x, keys):
	if type(keys) == str: return keys in x
	if len(keys) == 0: return False
	if not keys[0] in x: return False
	if len(keys) == 1: return True
	if not keys[1] in x[keys[0]]: return False
	if len(keys) == 2: return True
	if not keys[2] in x[keys[0]][keys[1]]: return False
	if len(keys) == 3: return True
	if not keys[3] in x[keys[0]][keys[1]][keys[2]]: return False
	if len(keys) == 4: return True
	if not keys[4] in x[keys[0]][keys[1]][keys[2]][keys[3]]: return False
	if len(keys) == 5: return True

def get_value(x, keys, default=None):
	if has_key(x, keys):
		if len(keys) == 1:
			return x[keys[0]]
		if len(keys) == 2:
			return x[keys[0]][keys[1]]
		if len(keys) == 3:
			return x[keys[0]][keys[1]][keys[2]]
		if len(keys) == 4:
			return x[keys[0]][keys[1]][keys[2]][keys[3]]
		if len(keys) == 5:
			return x[keys[0]][keys[1]][keys[2]][keys[3]][keys[4]]
	elif default != None:
		return default
	else:
		cli.error(f'No {keys}!')
