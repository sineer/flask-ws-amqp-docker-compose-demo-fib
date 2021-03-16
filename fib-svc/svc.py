import pika
import sys, os, time


url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')


def fib(n):
    a = 0
    b = 1
    c = None
    for i in range(1,n):
        c = a + b
        a = b
        b = c
    return c

def enqueue_response(res):
    global url

    print("Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        return "Failed to connect to AMQP!"

    channel = connection.channel()
    channel.exchange_declare(exchange='fibs',
                             exchange_type='fanout')

    # We send to 'fib_out'
    channel.queue_declare(queue='fib_out')
    channel.basic_publish(
        exchange='fibs',
        routing_key='fib_out',
        body=res)
    channel.queue_bind(exchange='fibs',
                       queue='fib_out')
    connection.close()

    ret = f"Sent Nth fibonacci number: {res} to AMQP 'fib_out' queue for processing..."
    print(ret, flush=True)
    return ret


def main():
    global url
    print("Trying to connect to AMQP...", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        time.sleep(3)
        main() # KEEP TRYING UNTIL RABBIT IS UP...
    channel = connection.channel()

    # We receive from 'fib_in'
    channel.queue_declare(queue='fib_in')

    def amqp_receive_callback(ch, method, properties, body):
        print(" [x] Received AMQP message from 'fib_in' queue! data: %r" % body, flush=True)
        res = fib(int(body))
        enqueue_response(str(res))

    # Consume AMQP messages...
    try:
        channel.basic_consume(amqp_receive_callback,
                              queue='fib_in',
                              no_ack=False)
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    print(' [*] Waiting for AMQP messages from fib_in queue...', flush=True)
    channel.start_consuming()


if __name__ == '__main__':
    main()
