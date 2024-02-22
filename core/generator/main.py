from .generator_server import GeneratorServer


def main():
    server = GeneratorServer()
    server.run()


if __name__ == '__main__':
    main()

