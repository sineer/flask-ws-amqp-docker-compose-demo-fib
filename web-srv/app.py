from flask import Flask, render_template
import sys, os, time


app = Flask(__name__)
url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')


# route() decorator is used to define the URL where index() function is registered for
@app.route('/')
def index():
	return render_template('index.html')


@app.route('/fib/<num>')
def add(num):
    global url

    print("Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    # We send to 'fib_in'
    channel = connection.channel()
    channel.queue_declare(queue='fib_in')
    channel.basic_publish(exchange='',
                          routing_key='fib_in',
                          body=num)

    connection.close()

    ret = f"Sent Nth fibonacci number: {num}"
    print(ret, flush=True)
    return ret


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
