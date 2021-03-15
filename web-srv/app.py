from flask import Flask, render_template
import pika

app = Flask(__name__)

# route() decorator is used to define the URL where index() function is registered for
@app.route('/')
def index():
	return render_template('index.html')


@app.route('/fib/<num>')
def add(num):
    #Access the AMQP_URL environment variable and parse it (fallback to rabbit)
    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    print(f"Connecting to AMQP url: {url}", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit'))
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise
    channel = connection.channel()
    channel.queue_declare(queue='fibonacci', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='fibonacci',
        body=num,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    connection.close()
    ret = f"Sent Nth fibonacci number: {num}"
    print(ret, flush=True)
    return ret


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
