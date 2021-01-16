from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, "index.html", {})


def conversation(request, username):
    return render(
        request,
        "conversation.html",
        {
            "username": username,
        },
    )
