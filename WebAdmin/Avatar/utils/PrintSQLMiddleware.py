from django.db import connection
class PrintSQLMiddleware:
    def process_response(self,request,response):
        for sql in connection.queries:
            print sql   
        return response
    