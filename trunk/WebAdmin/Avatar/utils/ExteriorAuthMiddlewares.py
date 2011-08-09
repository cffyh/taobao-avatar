from django.http import HttpResponseRedirect
class ExteriorAuthMiddlewares(object):
    def process_request(self,request):
        token = request.session.get('username')
        if token is None and not request.path.startswith('/login') and not request.path.startswith('/site_media') and not request.path.startswith('/svn')  and not request.path.startswith('/inter'):
            return HttpResponseRedirect("/login/")
