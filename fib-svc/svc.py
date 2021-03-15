import pika, os, time


def fib(n):
    a = 0
    b = 1
    c = None
    for i in range(1,n):
        c = a + b
        a = b
        b = c
    return c


def main():
    #Access the AMQP_URL environment variable and parse it (fallback to rabbit)
    url = os.environ.get('AMQP_URL', 'amqp://guest:guest@rabbit:5672/%2f')
    print(f"Connecting to AMQP url: {url}", flush=True)
    params = pika.URLParameters(url)
    try:
        connection = pika.BlockingConnection(params)
    except:
        time.sleep(1)
        main()
    channel = connection.channel()

    channel.queue_declare(queue='fibonacci')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body, flush=True)

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages...', flush=True)
    channel.start_consuming()


if __name__ == '__main__':
    main()
