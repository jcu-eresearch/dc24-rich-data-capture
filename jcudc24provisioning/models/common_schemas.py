import ast
import types
from jcudc24provisioning.views.deform_widgets import SelectMappingWidget, ConditionalCheckboxMapping
from beaker.cache import cache_region
import colander
import deform
from pyramid_deform import SessionFileUploadTempStore

__author__ = 'Casey Bajema'

#class TmpStore(dict):
#    """ Instances of this class implement the
#    :class:`deform.interfaces.FileUploadTempStore` interface"""
#    def preview_url(self, uid):
#        return None

#
#@cache_region('daily')
#def getJCUUsers():
#    pass

class OneOfDict(object):
    """ Validator which succeeds if the value passed to it is one of
    a fixed set of values """
    def __init__(self, choices):
        self.choices = choices

    def __call__(self, node, value):
        if not value in [x[0] for x in self.choices]:
            choices = ', '.join(['%s' % x[1] for x in self.choices])
            err = colander._('Please select one of ${choices}',
                    mapping={'choices':choices})
            raise colander.Invalid(node, err)

def _SelectMappingSchema__new__(cls, *args, **kw):
    if not "widget" in kw: kw["widget"] = SelectMappingWidget()

    node = object.__new__(cls.node_type)
    node.name = None
    node._order = next(colander.SchemaNode._counter)
    typ = cls.schema_type()

    node.__init__(typ, *args, **kw)

    node.children.insert(0,colander.SchemaNode(colander.String(), name="schema_select",
        widget = deform.widget.HiddenWidget(), missing="none"))

    for n in cls.nodes:
        node.add(n)

    return node

SelectMappingSchema = colander._SchemaMeta('SelectMappingSchema', (object,),
    dict(schema_type=colander.Mapping,
        node_type=colander.SchemaNode,
        __new__=_SelectMappingSchema__new__))

def _ConditionalCheckboxSchema__new__(cls, *args, **kw):
    if not "widget" in kw: kw["widget"] = ConditionalCheckboxMapping()

    node = object.__new__(cls.node_type)
    node.name = None
    node._order = next(colander.SchemaNode._counter)
    typ = cls.schema_type()
    node.__init__(typ, *args, **kw)

    node.add(colander.SchemaNode(colander.Boolean(), name="conditional_checkbox", widget = deform.widget.HiddenWidget(), missing=colander.null))

    for n in cls.nodes:
        node.add(n)

    return node

ConditionalCheckboxSchema = colander._SchemaMeta('ConditionalCheckboxSchema', (object,),
    dict(schema_type=colander.Mapping,
        node_type=colander.SchemaNode,
        __new__=_ConditionalCheckboxSchema__new__))

#    schema_select = colander.SchemaNode(colander.String(), widget=deform.widget.HiddenWidget())
#
#    def __init__(self, **kw):
#        super(SelectMappingSchema, self).__init__('Schema', (object,),
#            dict(schema_type=colander.Mapping, node_type=colander.SchemaNode, _new__=colander._Schema__new__))
#        if not "widget" in kw: kw["widget"] = SelectMappingWidget(template="select_mapping")
#        print clsattrs


class MapRegion(colander.SequenceSchema):
    location = colander.SchemaNode(colander.String())


class MapRegionSchema(colander.SequenceSchema):
    location = MapRegion(widget=deform.widget.SequenceWidget(template='map_sequence'))

#    def __init__(self, typ=deform.FileData(), *children, **kw):
#        if not "widget" in kw: kw["widget"] = deform.widget.SequenceWidget(template='map_sequence')
#        colander.SchemaNode.__init__(self, typ, *children, **kw)

# Return the tempstore data so we can get the actual data later - the FileUploadWidget in deform makes it real difficult by setting the preview_url before adding the data...
def preview_url(self, name):
    file_data = self.tempstore
    return (self.tempdir, file_data)

# Customise the serialize method of FileUploadWidget to parse the string from DB into dict
def file_upload_serialize(self, field, cstruct, readonly=False):
    if cstruct in (deform.widget.null, None):
        cstruct = {}
    if cstruct:
        if isinstance(cstruct, unicode):
            cstruct_items = cstruct.split(",")
            new_cstruct = {}
            for item in cstruct_items:
                if 'preview_url' in item:
                    continue

                if 'filename' in item and not 'filename' in new_cstruct:
                    new_cstruct['filename'] = item.split(":")[1].strip().replace("u'", "").replace('\'', "").replace("}", "")
                if 'uid' in item and not 'uid' in new_cstruct:
                    new_cstruct['uid'] = item.split(":")[1].strip()[2:-2].replace("u'", "").replace('\'', "").replace("}", "")

            cstruct = new_cstruct
        uid = cstruct['uid']
        if not uid in self.tmpstore:
            self.tmpstore[uid] = cstruct

    template = readonly and self.readonly_template or self.template
    return field.renderer(template, field=field, cstruct=cstruct)

@colander.deferred
def upload_widget(node, kw):
    request = kw['request']
    tmp_store = SessionFileUploadTempStore(request)
    tmp_store.preview_url = types.MethodType(preview_url, tmp_store)
    widget = deform.widget.FileUploadWidget(tmp_store)
    widget.serialize = types.MethodType(file_upload_serialize, widget)
    return widget


class Attachment(colander.SchemaNode):
    def __init__(self, typ=deform.FileData(), *children, **kw):
        if not "widget" in kw: kw["widget"] = upload_widget
        if not "title" in kw: kw["title"] = "Attach File"
        colander.SchemaNode.__init__(self, typ, *children, **kw)

#def deferred_upload_widget(field, bindargs):
#    request = bindargs['request']
#    session = request.session
#    tmpstore = TmpStore(session)
#    return deform.widget.FileUploadWidget(tmpstore)
#
#class MyUploadSchema(colander.Schema):
#    upload = colander.SchemaNode(deform.FileData(),
#        widget=deferred_upload_widget)
#
#schema = MyUploadSchema().bind(request=request)


#class Attachment(colander.SchemaNode):
#    attachment = MemoryTmpStore()
#
#    def __init__(self, typ=deform.FileData(), *children, **kw):
#        if not "widget" in kw: kw["widget"] = deform.widget.FileUploadWidget(self.attachment)
#        if not "missing" in kw: kw["missing"] = self.attachment
#        if not "title" in kw: kw["title"] = "Attach File"
#        colander.SchemaNode.__init__(self, typ, *children, **kw)

class Notes(colander.SequenceSchema):
    note = colander.SchemaNode(colander.String(), widget=deform.widget.TextAreaWidget())


class Email(colander.SchemaNode):
    def __init__(self, typ=colander.String(), *children, **kw):
        if not "title" in kw: kw["title"] = "Email"
        if not "validator" in kw: kw["validator"] = colander.Email()
        colander.SchemaNode.__init__(self, typ, *children, **kw)


class Person(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), title="Title",placeholder="eg. Mr, Mrs, Dr",)
    given_name = colander.SchemaNode(colander.String(), title="Given name")
    family_name = colander.SchemaNode(colander.String(), title="Family name")
    email = Email(missing="")


class People(colander.SequenceSchema):
    person = Person()


class Website(colander.MappingSchema):
    title = colander.SchemaNode(colander.String(), title="Title", placeholder="eg. Great Project Website", widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    url = colander.SchemaNode(colander.String(), title="URL", placeholder="eg. http://www.somewhere.com.au", widget=deform.widget.TextInputWidget(css_class="full_width", size=40))
    notes = colander.SchemaNode(colander.String(), title="Notes", missing="", placeholder="eg. This article provides additional information on xyz", widget=deform.widget.TextInputWidget(css_class="full_width", size=40))


class WebsiteSchema(colander.SequenceSchema):
    resource = Website(widget=deform.widget.MappingWidget(template="inline_mapping"))

countries = (
    ('AF', 'Afghanistan'),
    ('AX', 'Aland Islands'),
    ('AL', 'Albania'),
    ('DZ', 'Algeria'),
    ('AS', 'American Samoa'),
    ('AD', 'Andorra'),
    ('AO', 'Angola'),
    ('AI', 'Anguilla'),
    ('AQ', 'Antarctica'),
    ('AG', 'Antigua and Barbuda'),
    ('AR', 'Argentina'),
    ('AM', 'Armenia'),
    ('AW', 'Aruba'),
    ('AU', 'Australia'),
    ('AT', 'Austria'),
    ('AZ', 'Azerbaijan'),
    ('BS', 'Bahamas'),
    ('BH', 'Bahrain'),
    ('BD', 'Bangladesh'),
    ('BB', 'Barbados'),
    ('BY', 'Belarus'),
    ('BE', 'Belgium'),
    ('BZ', 'Belize'),
    ('BJ', 'Benin'),
    ('BM', 'Bermuda'),
    ('BT', 'Bhutan'),
    ('BO', 'Bolivia'),
    ('BA', 'Bosnia and Herzegovina'),
    ('BW', 'Botswana'),
    ('BV', 'Bouvet Island'),
    ('BR', 'Brazil'),
    ('IO', 'British Indian Ocean Territory'),
    ('BN', 'Brunei Darussalam'),
    ('BG', 'Bulgaria'),
    ('BF', 'Burkina Faso'),
    ('BI', 'Burundi'),
    ('KH', 'Cambodia'),
    ('CM', 'Cameroon'),
    ('CA', 'Canada'),
    ('CV', 'Cape Verde'),
    ('KY', 'Cayman Islands'),
    ('CF', 'Central African Republic'),
    ('TD', 'Chad'),
    ('CL', 'Chile'),
    ('CN', 'China'),
    ('CX', 'Christmas Island'),
    ('CC', 'Cocos (Keeling) Islands'),
    ('CO', 'Colombia'),
    ('KM', 'Comoros'),
    ('CG', 'Congo'),
    ('CD', 'Congo, The Democratic Republic of The'),
    ('CK', 'Cook Islands'),
    ('CR', 'Costa Rica'),
    ('CI', 'Cote D\'ivoire'),
    ('HR', 'Croatia'),
    ('CU', 'Cuba'),
    ('CY', 'Cyprus'),
    ('CZ', 'Czech Republic'),
    ('DK', 'Denmark'),
    ('DJ', 'Djibouti'),
    ('DM', 'Dominica'),
    ('DO', 'Dominican Republic'),
    ('EC', 'Ecuador'),
    ('EG', 'Egypt'),
    ('SV', 'El Salvador'),
    ('GQ', 'Equatorial Guinea'),
    ('ER', 'Eritrea'),
    ('EE', 'Estonia'),
    ('ET', 'Ethiopia'),
    ('FK', 'Falkland Islands (Malvinas)'),
    ('FO', 'Faroe Islands'),
    ('FJ', 'Fiji'),
    ('FI', 'Finland'),
    ('FR', 'France'),
    ('GF', 'French Guiana'),
    ('PF', 'French Polynesia'),
    ('TF', 'French Southern Territories'),
    ('GA', 'Gabon'),
    ('GM', 'Gambia'),
    ('GE', 'Georgia'),
    ('DE', 'Germany'),
    ('GH', 'Ghana'),
    ('GI', 'Gibraltar'),
    ('GR', 'Greece'),
    ('GL', 'Greenland'),
    ('GD', 'Grenada'),
    ('GP', 'Guadeloupe'),
    ('GU', 'Guam'),
    ('GT', 'Guatemala'),
    ('GG', 'Guernsey'),
    ('GN', 'Guinea'),
    ('GW', 'Guinea-bissau'),
    ('GY', 'Guyana'),
    ('HT', 'Haiti'),
    ('HM', 'Heard Island and Mcdonald Islands'),
    ('VA', 'Holy See (Vatican City State)'),
    ('HN">Honduras'),
    ('HK', 'Hong Kong'),
    ('HU', 'Hungary'),
    ('IS', 'Iceland'),
    ('IN', 'India'),
    ('ID', 'Indonesia'),
    ('IR', 'Iran, Islamic Republic of'),
    ('IQ', 'Iraq'),
    ('IE', 'Ireland'),
    ('IM', 'Isle of Man'),
    ('IL', 'Israel'),
    ('IT', 'Italy'),
    ('JM', 'Jamaica'),
    ('JP', 'Japan'),
    ('JE', 'Jersey'),
    ('JO', 'Jordan'),
    ('KZ', 'Kazakhstan'),
    ('KE', 'Kenya'),
    ('KI', 'Kiribati'),
    ('KP', 'Korea, Democratic People\'s Republic of'),
    ('KR', 'Korea, Republic of'),
    ('KW', 'Kuwait'),
    ('KG', 'Kyrgyzstan'),
    ('LA', 'Lao People\'s Democratic Republic'),
    ('LV', 'Latvia'),
    ('LB', 'Lebanon'),
    ('LS', 'Lesotho'),
    ('LR', 'Liberia'),
    ('LY', 'Libyan Arab Jamahiriya'),
    ('LI', 'Liechtenstein'),
    ('LT', 'Lithuania'),
    ('LU', 'Luxembourg'),
    ('MO', 'Macao'),
    ('MK', 'Macedonia, The Former Yugoslav Republic of'),
    ('MG', 'Madagascar'),
    ('MW', 'Malawi'),
    ('MY', 'Malaysia'),
    ('MV', 'Maldives'),
    ('ML', 'Mali'),
    ('MT', 'Malta'),
    ('MH', 'Marshall Islands'),
    ('MQ', 'Martinique'),
    ('MR', 'Mauritania'),
    ('MU', 'Mauritius'),
    ('YT', 'Mayotte'),
    ('MX', 'Mexico'),
    ('FM', 'Micronesia, Federated States of'),
    ('MD', 'Moldova, Republic of'),
    ('MC', 'Monaco'),
    ('MN', 'Mongolia'),
    ('ME', 'Montenegro'),
    ('MS', 'Montserrat'),
    ('MA', 'Morocco'),
    ('MZ', 'Mozambique'),
    ('MM', 'Myanmar'),
    ('NA', 'Namibia'),
    ('NR', 'Nauru'),
    ('NP', 'Nepal'),
    ('NL', 'Netherlands'),
    ('AN', 'Netherlands Antilles'),
    ('NC', 'New Caledonia'),
    ('NZ', 'New Zealand'),
    ('NI', 'Nicaragua'),
    ('NE', 'Niger'),
    ('NG', 'Nigeria'),
    ('NU', 'Niue'),
    ('NF', 'Norfolk Island'),
    ('MP', 'Northern Mariana Islands'),
    ('NO', 'Norway'),
    ('OM', 'Oman'),
    ('PK', 'Pakistan'),
    ('PW', 'Palau'),
    ('PS', 'Palestinian Territory, Occupied'),
    ('PA', 'Panama'),
    ('PG', 'Papua New Guinea'),
    ('PY', 'Paraguay'),
    ('PE', 'Peru'),
    ('PH', 'Philippines'),
    ('PN', 'Pitcairn'),
    ('PL', 'Poland'),
    ('PT', 'Portugal'),
    ('PR', 'Puerto Rico'),
    ('QA', 'Qatar'),
    ('RE', 'Reunion'),
    ('RO', 'Romania'),
    ('RU', 'Russian Federation'),
    ('RW', 'Rwanda'),
    ('SH', 'Saint Helena'),
    ('KN', 'Saint Kitts and Nevis'),
    ('LC', 'Saint Lucia'),
    ('PM', 'Saint Pierre and Miquelon'),
    ('VC', 'Saint Vincent and The Grenadines'),
    ('WS', 'Samoa'),
    ('SM', 'San Marino'),
    ('ST', 'Sao Tome and Principe'),
    ('SA', 'Saudi Arabia'),
    ('SN', 'Senegal'),
    ('RS', 'Serbia'),
    ('SC', 'Seychelles'),
    ('SL', 'Sierra Leone'),
    ('SG', 'Singapore'),
    ('SK', 'Slovakia'),
    ('SI', 'Slovenia'),
    ('SB', 'Solomon Islands'),
    ('SO', 'Somalia'),
    ('ZA', 'South Africa'),
    ('GS', 'South Georgia and The South Sandwich Islands'),
    ('ES', 'Spain'),
    ('LK', 'Sri Lanka'),
    ('SD', 'Sudan'),
    ('SR', 'Suriname'),
    ('SJ', 'Svalbard and Jan Mayen'),
    ('SZ', 'Swaziland'),
    ('SE', 'Sweden'),
    ('CH', 'Switzerland'),
    ('SY', 'Syrian Arab Republic'),
    ('TW', 'Taiwan, Province of China'),
    ('TJ', 'Tajikistan'),
    ('TZ', 'Tanzania, United Republic of'),
    ('TH', 'Thailand'),
    ('TL', 'Timor-leste'),
    ('TG', 'Togo'),
    ('TK', 'Tokelau'),
    ('TO', 'Tonga'),
    ('TT', 'Trinidad and Tobago'),
    ('TN', 'Tunisia'),
    ('TR', 'Turkey'),
    ('TM', 'Turkmenistan'),
    ('TC', 'Turks and Caicos Islands'),
    ('TV', 'Tuvalu'),
    ('UG', 'Uganda'),
    ('UA', 'Ukraine'),
    ('AE', 'United Arab Emirates'),
    ('GB', 'United Kingdom'),
    ('US', 'United States'),
    ('UM', 'United States Minor Outlying Islands'),
    ('UY', 'Uruguay'),
    ('UZ', 'Uzbekistan'),
    ('VU', 'Vanuatu'),
    ('VE', 'Venezuela'),
    ('VN', 'Viet Nam'),
    ('VG', 'Virgin Islands, British'),
    ('VI', 'Virgin Islands, U.S.'),
    ('WF', 'Wallis and Futuna'),
    ('EH', 'Western Sahara'),
    ('YE', 'Yemen'),
    ('ZM', 'Zambia'),
    ('ZW', 'Zimbabwe'),
    )

class Address(colander.MappingSchema):
    street1 = colander.SchemaNode(colander.String(), title="Street")
    street2 = colander.SchemaNode(colander.String(), title="Street", missing="")
    city = colander.SchemaNode(colander.String(), title="City")
    country = colander.SchemaNode(colander.String(), title="Country",
        widget=deform.widget.SelectWidget(values=countries), validator=colander.OneOf(countries))
    state = colander.SchemaNode(colander.String(), title="State")
    post_code = colander.SchemaNode(colander.String(), title="Post Code")