#from pyramid.view import view_config
#from deform import Form
#from deform import ValidationFailure
#from general_schema import ProjectData
#
#from layouts import Layouts
#
#class ProvisioningViews(Layouts):
#    def __init__(self, request):
#        self.request = request
#
#    @view_config(renderer="../templates/dashboard.pt")
#    def dashboard_view(self):
#        return {"page_title": "Provisioning Dashboard"}
#
#    @view_config(renderer="../templates/metadata.pt", name="metadata")
#    def metadata_view(self):
#        return {"page_title": "Metadata Collection"}
#
#    @view_config(renderer="../templates/data_types.pt", name="data_types")
#    def types_view(self):
#        return {"page_title": 'Data Types'}
#
#    @view_config(renderer="../templates/data_storage.pt", name="data_storage")
#    def storage_view(self):
#        return {"page_title": "Data Processing & Storage"}
#
#
#    @view_config(renderer='../templates/data_inputs.pt', name='data_inputs')
#    def inputs_view(request):
#        return {'page_title': 'Data Inputs'}
#
#    @view_config(renderer='../templates/activate.pt', name='activate')
#    def activate_view(request):
#        return {'page_title': 'Activate'}
#
#
#
#
#        #    try:
#    #        one = DBSession.query(MyModel).filter(MyModel.name=='one').first()
#    #    except DBAPIError:
#    #        return Response(conn_err_msg, content_type='text/plain', status_int=500)
#    #    return {'one':one, 'project':'ProvisioningInterface'}
#    #
#    #conn_err_msg = """\
#    #Pyramid is having a problem using your SQL database.  The problem
#    #might be caused by one of the following things:
#    #
#    #1.  You may need to run the "initialize_ProvisioningInterface_db" script
#    #    to initialize your database tables.  Check your virtual
#    #    environment's "bin" directory for this script and try to run it.
#    #
#    #2.  Your database server may not be running.  Check that the
#    #    database server referred to by the "sqlalchemy.url" setting in
#    #    your "development.ini" file is running.
#    #
#    #After you fix the problem, please restart the Pyramid application to
#    #try it again.
#    #"""
