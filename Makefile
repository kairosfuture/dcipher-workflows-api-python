publish:
	poetry lock --no-update
	poetry build
	poetry publish
