def user_role(request):
    return {'user_role': request.session.get('user_role', 'DEPT_USER')}
