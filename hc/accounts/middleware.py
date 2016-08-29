from hc.accounts.models import Profile


class TeamAccessMiddleware(object):
    def process_request(self, request):
        if not request.user.is_authenticated():
            return

        teams_q = Profile.objects.filter(member__user_id=request.user.id)
        teams_q = teams_q.select_related("user")
        request.teams = list(teams_q)

        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile(user=request.user)
            profile.save()

        if profile.current_team:
            request.team = profile.current_team
        else:
            request.team = profile
