from flask import Flask, render_template
import pika

app = Flask(__name__)

# route() decorator is used to define the URL where index() function is registered for
@app.route('/')
def index():
	return render_template('index.html')


@app.route('/fib/<num>')
def add(num):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbit'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='task_queue',
        body=num,
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))
    connection.close()
    return " [x] Sent: %s" % num


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
