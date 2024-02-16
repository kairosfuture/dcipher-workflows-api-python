publish:
	poetry lock --no-update
	poetry export --output requirements.txt
	poetry build
	poetry publish
