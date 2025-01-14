from potlako_subject.models import BaselineClinicalSummary, NavigationSummaryAndPlan
import re
from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from edc_base.view_mixins import EdcBaseViewMixin
from edc_constants.constants import YES
from edc_navbar import NavbarViewMixin

from edc_dashboard.view_mixins import (
    ListboardFilterViewMixin, SearchFormViewMixin)
from edc_dashboard.views import ListboardView

from ..model_wrappers import NavigationWorkListModelWrapper
from ..models import NavigationWorkList
from .filters import NavigationListboardViewFilters
from .worklist_queryset_view_mixin import WorkListQuerysetViewMixin


class NavigationListboardView(NavbarViewMixin, EdcBaseViewMixin,
                              ListboardFilterViewMixin, SearchFormViewMixin,
                              WorkListQuerysetViewMixin,
                              ListboardView):

    listboard_template = 'potlako_navigation_listboard_template'
    listboard_url = 'potlako_navigation_listboard_url'
    listboard_panel_style = 'info'
    listboard_fa_icon = "fa-user-plus"

    model = 'potlako_follow.navigationworklist'
    listboard_view_filters = NavigationListboardViewFilters()
    model_wrapper_cls = NavigationWorkListModelWrapper
    navbar_name = 'potlako_follow'
    navbar_selected_item = 'navigation_worklist'
    ordering = '-modified'
    paginate_by = 10
    search_form_url = 'potlako_navigation_listboard_url'

    @property
    def create_worklist(self):
        subject_visit_cls = django_apps.get_model('potlako_subject.subjectvisit')
        subject_identifiers = subject_visit_cls.objects.values_list(
            'subject_identifier', flat=True).filter(visit_code=1000)
        subject_identifiers = list(set(subject_identifiers))
        for subject_identifier in subject_identifiers:
            try:
                BaselineClinicalSummary.objects.get(subject_identifier=subject_identifier,
                                                    team_discussion=YES)
            except BaselineClinicalSummary.DoesNotExist:
                if self.get_community_arm(subject_identifier) == 'Intervention':
                    try:
                        NavigationSummaryAndPlan.objects.get(
                            subject_identifier=subject_identifier)
                    except NavigationSummaryAndPlan.DoesNotExist:
                        try:
                            NavigationWorkList.objects.get(
                                subject_identifier=subject_identifier)
                        except NavigationWorkList.DoesNotExist:
                            NavigationWorkList.objects.create(
                                subject_identifier=subject_identifier)
                    else:
                        NavigationWorkList.objects.filter(
                            subject_identifier=subject_identifier).delete()
                else:
                    NavigationWorkList.objects.filter(
                            subject_identifier=subject_identifier).delete()
            else:
                try:
                    NavigationWorkList.objects.get(subject_identifier=subject_identifier)
                except NavigationWorkList.DoesNotExist:
                    NavigationWorkList.objects.create(
                        subject_identifier=subject_identifier)

    def get_success_url(self):
        return reverse('potlako_follow:potlako_navigation_listboard_url')

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset_filter_options(self, request, *args, **kwargs):
        options = super().get_queryset_filter_options(request, *args, **kwargs)
        if kwargs.get('subject_identifier'):
            options.update(
                {'subject_identifier': kwargs.get('subject_identifier')})
        return options

    def extra_search_options(self, search_term):
        q = Q()
        if re.match('^[a-zA-Z]+$', search_term):
            q = Q(village_town__icontains=search_term)
        return q

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.create_worklist
        context.update(
        )
        return context

    def get_community_arm(self, subject_identifier):
        onschedule_model_cls = django_apps.get_model(
            'potlako_subject.onschedule')
        try:
            onschedule_obj = onschedule_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except onschedule_model_cls.DoesNotExist:
            return None
        else:
            return onschedule_obj.community_arm
