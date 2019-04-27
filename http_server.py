import socket
import sys
import traceback
import os
import mimetypes


def response_ok(body=b"This is a minimal response", mimetype=b"text/plain"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->

        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """

    return b"\r\n".join([
           b"HTTP/1.1 200 OK",
           b"Content-Type: " + mimetype,
           b"",
           body
    ])


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""

    return b"\r\n".join([
            b"HTTP/1.1 405 Method Not Allowed",
            b"Content-Type: text/html",
            b"",
            b"<html><h1>The request method is not allowed...",
            b"</h1></html>"])


def response_not_found():
    """Returns a 404 Not Found response"""

    return b"\r\n".join([
            b"HTTP/1.1 404 Not Found",
            b"Content-Type: text/plain",
            b"",
            b"Error encountered while visiting"])


def parse_request(request):
    """
    Given the content of an HTTP request, returns the path of that request.

    This server only handles GET requests, so this method shall raise a
    NotImplementedError if the method of the request is not GET.
    """

    if 'GET' not in request:
        raise NotImplementedError
    else:
        return request.split()[1]


def response_path(path):
    """
    This method should return appropriate content and a mime type.

    If the requested path is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the path is a file, it should return the contents of that file
    and its correct mimetype.

    If the path does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        response_path('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        response_path('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        response_path('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        response_path('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """

    webroot_path = os.path.join(os.getcwd(), 'webroot' + path)

    # Raise a NameError if the requested content is not present under webroot.
    if not os.path.exists(webroot_path):
        raise NameError

    # If the path is a file, return the contents and mimetype of that file
    if os.path.isfile(webroot_path):

        try:
            # Guesses the correct mimetype of the given file
            mime_type = mimetypes.guess_type(webroot_path)[0].encode()
            # returns the content of the file
            with open(webroot_path, "rb") as file:
                content = file.read()
        except Exception:
            raise NameError
    else:
        # Lists the contents of the directory with a `text/plain' mimetype.
        mime_type = b"text/plain"
        content = "\r\n".join(os.listdir(webroot_path)).encode()

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)

                request = ''
                while True:
                    data = conn.recv(1024)
                    request += data.decode('utf8')

                    if '\r\n\r\n' in request:
                        break

                print("Request received:\n{}\n\n".format(request))

                try:
                    # Uses parse_request to retrieve the path from the request.
                    path = parse_request(request)

                    # Retrieves the content and the mimetype, based on the request path.
                    content, mimetype = response_path(path)

                    # Uses the content and mimetype from response_path to build a response_ok.
                    response = response_ok(
                        body=content,
                        mimetype=mimetype
                    )

                except NotImplementedError:
                    # NotImplementedError raises a method_not_allowed response.
                    response = response_method_not_allowed()
                except NameError:
                    # NameError raises a a not_found response.
                    response = response_not_found()

                conn.sendall(response)
            except Exception as e:
                traceback.print_exc()
            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return
    except Exception as e:
        traceback.print_exc()


if __name__ == '__main__':
    server()
    sys.exit(0)
