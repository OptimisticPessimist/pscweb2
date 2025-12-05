import azure.functions as func
from azure.functions import AsgiFunctionApp
from pscweb2.asgi import application

app = AsgiFunctionApp(app=application, http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="*")
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    return func.AsgiMiddleware(application).handle(req, context)
