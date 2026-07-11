from ros import create_app
from ros.shared.exceptions import ROSException

app = create_app()

@app.route('/raise')
def raise_error():
    raise ROSException('boom', 418)

client = app.test_client()
response = client.get('/raise')
print(response.status_code)
print(response.get_json())
