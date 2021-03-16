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

    # We send to 'fib_out'
    channel = connection.channel()
    channel.queue_declare(queue='fib_out')
    channel.basic_publish(exchange='',
                          routing_key='fib_out',
                          body=res)

    connection.close()

    ret = f"Sent fibonacci number: {res} to AMQP 'fib_out' queue for processing..."
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

        try:
            num = int(body)
            print(f"Received Nth fibonacci #: {num}")
            res = fib(num)
            print(f"Fibonacci for the Nth #{num} is: {res}")
            enqueue_response(str(res))
        except:
            print(f"failed to cast body: {body} into an integer!", flush=True)

    # Consume AMQP messages...
    try:
        channel.basic_consume(amqp_receive_callback,
                              queue='fib_in')
    except:
        print("Unexpected error:", sys.exc_info()[0], flush=True)
        raise

    print(' [*] Waiting for AMQP messages from fib_in queue...', flush=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    print("Goodbye!", flush=True)


if __name__ == '__main__':
    main()
