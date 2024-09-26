from django.core.management.base import BaseCommand
from gee_api.models import State, District, SubDistrict, Village
from typing import List, Dict


class Command(BaseCommand):
    help = 'Populate the RDS instance with location data for states, districts, sub-districts, and villages'

    def add_villages(self, subdistrict: SubDistrict, villages: List[str]) -> None:
        """
        Adds villages to a given subdistrict.

        Args:
            subdistrict (SubDistrict): The subdistrict to which the villages belong.
            villages (List[str]): A list of village names.
        """
        for village_name in villages:
            Village.objects.get_or_create(name=village_name, subdistrict=subdistrict)
        self.stdout.write(self.style.SUCCESS(f'Added villages to {subdistrict.name}'))

    def add_subdistricts(self, district: District, subdistricts_and_villages: Dict[str, List[str]]) -> None:
        """
        Adds subdistricts and their corresponding villages to a given district.

        Args:
            district (District): The district to which the subdistricts belong.
            subdistricts_and_villages (Dict[str, List[str]]): A dictionary where the keys are subdistrict names
                                                             and the values are lists of village names.
        """
        for subdistrict_name, villages in subdistricts_and_villages.items():
            subdistrict, created = SubDistrict.objects.get_or_create(name=subdistrict_name, district=district)
            self.add_villages(subdistrict, villages)
        self.stdout.write(self.style.SUCCESS(f'Added subdistricts to {district.name}'))

    def add_districts(self, state: State, districts_and_subdistricts: Dict[str, Dict[str, List[str]]]) -> None:
        """
        Adds districts and their corresponding subdistricts to a given state.

        Args:
            state (State): The state to which the districts belong.
            districts_and_subdistricts (Dict[str, Dict[str, List[str]]]): A dictionary where the keys are district names,
                                                                          the values are dictionaries that map subdistrict
                                                                          names to lists of village names.
        """
        for district_name, subdistricts in districts_and_subdistricts.items():
            district, created = District.objects.get_or_create(name=district_name, state=state)
            self.add_subdistricts(district, subdistricts)
        self.stdout.write(self.style.SUCCESS(f'Added districts to {state.name}'))

    def handle(self, *args, **kwargs) -> None:
        """
        Handles the command to populate location data.
        """
        # Example data for Rajasthan
        rajasthan_data = {
            'Karauli': {
                'Todabhim': [
                    'anatpura', 'bhanakpura', 'bhaiseena', 'tudawali', 'bhajera', 'dantli', 'mehandipur', 'gahroli',
                    'sankarwara', 'bhooda', 'parla khalsa', 'parla jageer', 'shankarpur dorka', 'sarsena chak no-1',
                    'muthepur', 'jhareesa', 'bhaisapatti khurd', 'bhaisapatti kalan', 'choorpura', 'madhopura', 'matasoola',
                    'parli khurd', 'jodhpura', 'khirkhiri', 'nangal mandal', 'vishanpura charan', 'azizpur', 'mirzapur',
                    'gopalpura', 'mahendwara', 'asro', 'makbara', 'kaneti', 'bheempur', 'sujanpura', 'sehrakar', 'dadanpur',
                    'mannauj', 'nandipur', 'trishool', 'jhunki', 'jaisni', 'kheri', 'mereda', 'turakpur', 'manderoo',
                    'gazipur', 'chak gazipur', 'kheriya', 'dorawali', 'kamalpuriya ka pura', 'jonl', 'vishan pura', 'bonl',
                    'kariri', 'khanpur', 'fatehpur', 'mohanpur', 'bholooki kothi', 'balawas', 'kudhawal', 'shankarpur',
                    'nangal sultanpur', 'faujipur', 'badleta khurd', 'machri', 'beejalwara', 'ladpur', 'edalpur',
                    'bhandari androoni', 'rajor', 'makhthot', 'monapura', 'khohra', 'padampura', 'gajjupura', 'bairoj',
                    'gorda', 'rajoli', 'dhawan', 'nand', 'mohanpura', 'gaonri', 'kamalpura', 'jahannagar morda',
                    'bhandari berooni', 'nangal sherpur', 'balghat', 'penchla', 'ghatra sherpur', 'parli', 'badleta bujrg',
                    'baledi', 'moondiya', 'salaipura', 'majeedpura', 'karampura', 'pat katara', 'jaisinghpura',
                    'jagdishpura', 'mahmadpur', 'deolen', 'nayagaon', 'peelwa', 'ranmalpara', 'tighriya', 'mosalpur',
                    'chak kanwar pura', 'kanwar pura', 'lalaram ka pura', 'bhadoli', 'singhniya', 'salimpur', 'katara aziz',
                    'lapawali', 'tajpur', 'kanjoli', 'pahari', 'kuteela', 'bichpuri', 'urdain', 'khilchipur meena',
                    'khilchipur bara', 'barh mahasinghpura', 'luhar khera', 'chandwar', 'mahswa', 'bhotwara', 'ayyapur',
                    'kirwara', 'arej', 'shekh pura', 'ranoli', 'kalwari', 'akhawara', 'gazipur', 'bahadurpur', 'bhopur',
                    'sahjanpur', 'nisoora'
                ],
                'Nadoti': [
                    'chainpura', 'meenapatti', 'rampura', 'sandera', 'rajpur', 'talchida', 'garhi', 'bara', 'timawa',
                    'dholeta', 'andhiya khera', 'barh kemri', 'bheelapara', 'balakhera', 'maloopara', 'ghatoli',
                    'rengaspura', 'gurha chandraji', 'gidani', 'rajahera', 'muhana', 'guna', 'bhanwarwara', 'jahra',
                    'machri', 'khurd', 'bhanwra', 'nayawas', 'gothra', 'dhadanga', 'dhahariya', 'nadoti', 'sikandarpur',
                    'ibrahimpur', 'bara wajidpur', 'dhamadi ka pura', 'mehta ka pura', 'maidhe ka pura', 'jindon ka pura',
                    'dhand ka pura', 'kaimri', 'tesgaon', 'kakala', 'bilai', 'ralawata', 'khedla', 'ronsi', 'kemla',
                    'milak saray', 'kunjela', 'kherli', 'nayapura', 'baragaon', 'hodaheli', 'kaima', 'bardala', 'jeerna',
                    'alooda', 'dalpura', 'jeetkipur', 'loda', 'harloda', 'pal', 'lalsar', 'bhondwara', 'ganwari',
                    'chirawanda', 'dhola danta', 'garhmora', 'rupadi', 'raisana', 'garhkhera', 'khoyli', 'palri', 'salawad',
                    'bagor', 'bamori', 'gurli', 'garhi khempur', 'khura chainpura', 'shahar', 'lahawad', 'sop',
                    'bara pichanot', 'sanwta'
                ],
                'Hindaun': [
                    'ghonsla', 'kherli goojar', 'atkoli', 'churali', 'pali', 'singhan jatt', 'reenjhwas', 'bai jatt',
                    'dhursi', 'vijaypura', 'ber khera', 'sitapur', 'chandeela', 'gudhapol', 'mahoo ibrahimpur', 'karai',
                    'mahoo khas', 'mahoo dalalpur', 'shyampur moondri', 'fazalabad', 'peepalhera', 'dhahara',
                    'gadhi panbheda', 'gadhi mosamabad', 'sikandarpur', 'gopipur', 'kyarda khurd', 'patti narayanpur',
                    'kyarda kalan', 'rewai', 'lahchora', 'hukmi khera', 'dhindhora', 'dhandhawali', 'suroth', 'taharpur',
                    'bhukrawali', 'jatwara', 'durgasi', 'kheri hewat', 'somala ratra', 'somli', 'khijoori', 'sherpur',
                    'jat nagala', 'bahadurpur', 'alawara', 'bajna khurd', 'vajna kalan', 'banki', 'ekorasi', 'mukandpura',
                    'barh karsoli', 'kalwari jatt', 'rara shahpur', 'hadoli', 'chinayata', 'kheep ka pura', 'kalyanpur sayta',
                    'khareta', 'areni goojar', 'mothiyapur', 'jhirna', 'ponchhri', 'barh ponchhri', 'jewarwadaatak',
                    'bhango', 'khohara ghuseti', 'chamar pura', 'phulwara', 'sikroda jatt', 'sikroda meena', 'kheri sheesh',
                    'kheri ghatam', 'hindaun rural', 'kailash nagar', 'mandawara', 'jhareda', 'alipura', 'vargama',
                    'nagla meena', 'binega', 'jahanabad', 'irniya', 'kheri chandla', 'kajanipur', 'hingot', 'banwaripur',
                    'gaonri', 'dubbi', 'norangabad', 'akbarpur', 'kodiya', 'chandangaon', 'danalpur', 'kandroli',
                    'pataunda', 'sanet', 'khera', 'jamalpur', 'kutakpur', 'katkar', 'reethauli', 'garhi badhawa',
                    'gaonda meena', 'todoopura', 'gaoda goojar', 'gunsar', 'singhan meena', 'manema', 'kachroli',
                    'dedroli', 'bajheda', 'leeloti', 'kalwar meena', 'khanwara', 'kotra dhahar', 'kotri', 'kalakhana',
                    'palanpur'
                ],
                'Karauli': [
                    'sengarpura', 'ari hudpura', 'rod kalan', 'chak rod', 'rudor', 'baseri', 'ruggapura', 'jungeenpura',
                    'pahari', 'kashirampura', 'gurla', 'rod khurd', 'peepalpura', 'teekaitpura', 'unche ka pura',
                    'chorandapura', 'sahajpur', 'pareeta', 'raghuvanshi', 'mohanpur', 'bindapura', 'nayawas', 'jagatpura',
                    'barh gulal', 'jahangeerpur', 'deeppura', 'dafalpur', 'makanpur', 'barh dulhepal', 'bharka', 'beejalpur',
                    'pator', 'manthai', 'daleelpur', 'paitoli', 'saipur', 'keeratpura', 'hajaripura', 'dahmoli', 'tulsipura',
                    'kharenta', 'birwas', 'deeppura', 'balloopura', 'agarri', 'silpura', 'manchi', 'bhaisawat', 'shankarpur',
                    'pahari meeran', 'makanpur chaube', 'konder', 'sohanpura', 'chainpur', 'ummedpura', 'gadoli', 'fatehpur',
                    'mengra kalan', 'ledor kalan', 'mengra khurd', 'manda khera', 'hakimpura', 'kheriya', 'goojar bhavli',
                    'narayana', 'malpur', 'keshrisingh ka pura', 'rajanipura', 'pejpura', 'seeloti', 'unchagaon', 'madanpur',
                    'khera rajgarh', 'sakarghata', 'kumherpur', 'pura auodarkhan', 'lakhnipur', 'bhaua', 'nayawas',
                    'neemripura', 'dukawali', 'barwatpura', 'garhi', 'meola', 'chavadpura', 'tali', 'sadpura', 'peepal kherla',
                    'danda', 'nawlapura', 'timkoli', 'jamoora', 'umri', 'siganpur', 'mangrol', 'alampur', 'kanchanpur with talhati',
                    'singniya', 'farakpur', 'bhojpur', 'virhati', 'garh mandora', 'sewli', 'birhata', 'daudpur', 'piprani',
                    'deori', 'khooda', 'khoondri', 'keshpura', 'aneejara', 'munshipura', 'rohar', 'masalpur', 'rughpura',
                    'mardai khurd', 'khanpura', 'mardai kalan', 'bhood khera', 'lotda', 'sahanpur', 'kasara', 'bhavli',
                    'shubhnagar', 'guwreda', 'golara', 'ledor khurd', 'bhaua khera', 'khaira', 'bhauwapura', 'bahrai',
                    'ratiyapura', 'chhawar', 'kota chhawar', 'machani', 'tatwai', 'binega', 'sorya', 'kosra', 'bhoder',
                    'bichpuri', 'saseri', 'bhanwarpura', 'barkhera', 'dhandhupura', 'rajpur', 'thar ka pura', 'anandgarh',
                    'gunesari', 'dhoogarh', 'gopalpur sai', 'rampur', 'birhati', 'kalyani', 'mamchari', 'taroli', 'gunesra',
                    'manch', 'kota mam', 'harjanpura', 'barrif', 'gopalgarh', 'alampur', 'dalapura shastri', 'pator shastri',
                    'reechhoti', 'wajidpur', 'barriya', 'chainpur', 'khirkhira', 'hanumanpura', 'ghurakar', 'manoharpura',
                    'kashipura', 'semarda', 'gerai ki guwari', 'gangurda', 'gerai', 'lauhra', 'kailadevi', 'khohri',
                    'basai dulapura', 'atewa', 'arab ka pura', 'maholi', 'bawli', 'rajor', 'karsai', 'jakher', 'akolpura',
                    'doodapura', 'bhikam pura', 'khoobnagar', 'parasari', 'mahoo'
                ],
                'Mandrail': [
                    'garhi ka gaon', 'kanchanpur', 'batda', 'makanpur swami', 'bhankri', 'gurdah', 'naharpura', 'baharda',
                    'teen pokhar', 'langra', 'bugdar', 'doylepura', 'chandeli', 'rodhai', 'gurja', 'shyampur', 'needar',
                    'jagadarpura', 'khirkan', 'mogepura', 'garhwar', 'nayagaon', 'makanpur', 'bhattpura', 'bhojpur',
                    'mandrail', 'firojpur', 'ghatali', 'chainapura', 'jakhauda', 'rajpur', 'pasela', 'paseliya', 'baguriyapura',
                    'manakhur', 'chandelipura', 'darura', 'mureela', 'ond', 'bhorat', 'mar ka kua', 'bagpur', 'dhoreta',
                    'maikna', 'gopalpur', 'dargawan', 'rancholi', 'pancholi', 'nihalpur', 'tursampur', 'ranipura', 'barred'
                ],
                'Sapotra': [
                    'kherla', 'neemoda', 'edalpur', 'manda', 'meenapura', 'baroda', 'gordhanpura', 'jeerota', 'dayarampura',
                    'narauli', 'masawata', 'bairunda', 'harisinghpura', 'khidarpur', 'bhartoon', 'khirkhira', 'baloti',
                    'badh salempur', 'salempur', 'jatwari', 'rundi', 'govindpura', 'rampur palan', 'kurgaon', 'mahmadpur',
                    'mandawara', 'gokalpura', 'badh sariya', 'badh jeewansingh', 'badh kothimundha', 'badh pratapsingh',
                    'badh bhoodhar', 'hanjapur', 'thooma', 'dikoli khurd', 'khera', 'lediya', 'kudawada', 'dikoli kalan',
                    'kachroda', 'shekhpura', 'dabra', 'sadpura', 'kanapura', 'khirkhiri', 'looloj', 'peelodapura', 'inayati',
                    'jakhoda', 'aurach', 'raneta', 'jorli', 'kishorpura', 'doondipura', 'paharpura', 'adooda', 'ganwda',
                    'madhorajpura', 'ekat', 'rooppura', 'pardampura', 'gadhi ka gaon', 'hadoti', 'fatehpur', 'saimarda',
                    'kiradi', 'bagida', 'simar', 'khoh', 'unchi guwari', 'kala gurha', 'gorahar', 'bhandaripura', 'nisana',
                    'dabir', 'bookana', 'khanpur', 'choragaon', 'dhoolwas', 'khawda', 'gajjupura', 'jori', 'tursangpura',
                    'gopipura', 'keeratpura', 'ratanapura', 'baluapura', 'hariya ka mandir', 'gothra', 'suratpura', 'bapoti',
                    'mangrol', 'lokeshnagar', 'mijhaura', 'ada doongar', 'amarwar', 'narauli', 'bajna', 'budha bajna',
                    'ramthara', 'amargarh', 'doodha ki guwari', 'matoriya ki guwari', 'daulatpura', 'nainiya ki guwari',
                    'patipura', 'raseelpur jaga', 'marmada', 'raibeli jagman ki', 'khijoora', 'veeram ki guwari', 'nibhaira',
                    'moraichi', 'rawatpura', 'baharda', 'choriya khata', 'chorka khurd', 'chorka kalan', 'kanarda',
                    'chacheri', 'maharajpura', 'hasanpura', 'gota', 'chaurghan', 'bharrpura', 'amarapur', 'asha ki guwari',
                    'mahal dhankri', 'bhaironpura', 'nanpur', 'chirchiri', 'manki', 'kamokhari', 'dongri', 'dangariya',
                    'kankra', 'karanpur', 'ghusai', 'garhi ka gaon', 'karai', 'rahir', 'alwat ki guwari', 'chaube ki guwari',
                    'bahadarpur', 'mandi bhat', 'sonpura', 'raibeli mathuraki', 'amre ki guwari', 'koorat ki guwari',
                    'chirmil', 'arora', 'manikpura', 'toda', 'simara', 'kased'
                ],
            }
        }

        # Example data for Andhra Pradesh (Adilabad)
        andhra_pradesh_data = {
            'Adilabad': {
                'Tamsi': [
                    'karanji t', 'guledi', 'gomutri', 'antargaon', 'arli t', 'wadoor', 'dhanora', 'kamathwada', 'gona',
                    'gunjala', 'gollaghat', 'tamsi k', 'nipani', 'dabbakuchi', 'bheempoor', 'belsari rampur', 'anderband',
                    'girgaon', 'ambugaon', 'palodi ramnagar', 'wadgaon', 'khapperla', 'pippalkhoti', 'ghotkuri', 'savargaon',
                    'bandalnagapur', 'jamdi', 'tamsi b', 'waddadi', 'hasnapur', 'ponnari'
                ],
                'Adilabad': [
                    'jamdapur', 'dimma', 'pochara', 'rampoor royati', 'bheemseri', 'chanda', 'landasangvi', 'nishanghat',
                    'arli buzurg', 'takli', 'kumbhajheri', 'ramai', 'jamuldhari', 'yapalguda', 'anukunta', 'battisawargaon',
                    'mavala', 'kachkanti', 'tontoli', 'kottur nevegaon', 'borenur', 'lokari', 'ankoli', 'waghapur',
                    'maleborgaon', 'chinchughat', 'ankapoor', 'asodabhurki', 'pippaldhari', 'wanwat', 'belluri', 'khandala',
                    'lohara', 'hathigutta', 'tippa', 'maregaon', 'khanapoor', 'chichadhari', 'dasnapur', 'adilabad'
                ],
                'Jainad': [
                    'hathighat', 'guda', 'rampurtaraf', 'korta', 'kedarpur', 'akoli', 'gimma khurd', 'sirsonna', 'bhoraj',
                    'fouzpur', 'poosai', 'pipparwada', 'moudagada', 'kamai', 'dollara', 'pendalwada', 'lekarwadi',
                    'savapur', 'hashampur', 'tarada buzurg', 'nizampur', 'nirala', 'balapur', 'akurla', 'sangvi k',
                    'deepaiguda', 'kowtha', 'bahadurpur', 'kura', 'karanji', 'khapri', 'umri', 'belgaon', 'ballori',
                    'makoda', 'jainad', 'muktapur', 'ada', 'kamtha', 'pardi buzurg', 'pardi khurd', 'pippalgaon', 'laxmipur uligan',
                    'jamini', 'kanpa mediguda', 'mangurla'
                ],
                'Bela': [
                    'sangdi', 'bhedoda', 'guda', 'kamgarpur', 'manyarpur', 'khagdur', 'mangrool', 'kobhai', 'dehegaon',
                    'mohabatpur', 'bhodod kopsi', 'shamshabad', 'awalpur', 'sirsanna', 'takli', 'dhoptala', 'bela',
                    'patan', 'ramkam', 'ponnala', 'chandpalle', 'chaprala', 'warur', 'junoni', 'karoni k', 'ekori', 'masala buzurg',
                    'bhadi', 'masala khurd', 'syedpur', 'toyaguda kora', 'sahej', 'sangvi', 'douna', 'boregaon', 'pohar',
                    'karoni b', 'sadarpur', 'sonkhos', 'khadki', 'pitgaon'
                ],
                'Talamadugu': [
                    'kosai', 'palasi buzurg', 'palasi khurd', 'kuchalapoor', 'lingi', 'sunkidi', 'umadam', 'khodad',
                    'kajjarla', 'ruyyadi', 'kothur', 'talamadugu', 'dorli', 'kappardevi', 'dehegaon', 'umrei', 'ratnapur',
                    'jhari', 'saknapoor', 'arli khurd', 'devapur', 'lachampur', 'palle buzurg', 'bharampur', 'nandigaon',
                    'palle khurd'
                ],
                'Gudihathnoor': [
                    'vaijapur', 'kamalapur', 'seetagondi', 'malkapur', 'tosham', 'lingapur', 'gudihathinur', 'machapur',
                    'dhampur', 'muthnur', 'neradigonda', 'mannur', 'dongargaon', 'kolhari', 'umri b', 'guruj', 'gondharkapur',
                    'rendlabori', 'shantapur', 'belluri', 'tejapur'
                ],
                'Inderavelly': [
                    'pipri', 'devapur', 'ginnera', 'indervelly k', 'bursanpatar', 'gattepalle', 'dodanda', 'indervelly b',
                    'yamaikunta', 'muthnur', 'dhannura b', 'dhannura k', 'goureepur', 'mendapalle', 'keslapur', 'heerapur',
                    'harkapur', 'anji', 'mamidiguda', 'dasnapur', 'keslaguda', 'mallapur', 'dharmasagar', 'tejapur',
                    'lakampur', 'rampur b', 'kondapur', 'pochampalle', 'lachimpur k', 'waipet', 'lachimpur b', 'walganda heerapur',
                    'dongargaon', 'wadagaon'
                ],
                'Narnoor': [
                    'kondi', 'rampur', 'khandow', 'dongargaon', 'sedwai', 'kadodi', 'kouthala', 'kothapalle g', 'rupapur',
                    'warkwai', 'ademeyon', 'sawari', 'pipri', 'arjuni', 'paraswada k', 'lokari k', 'jhari', 'dhaba k',
                    'dhaba buzurg', 'punaguda', 'maregaon', 'gadiguda', 'kunikasa', 'kolama', 'parswada b', 'gouri', 'pownur',
                    'lokari b', 'khadki', 'sungapur', 'chorgaon', 'manjari', 'babjhari', 'dhupapur', 'empalle', 'sangvi',
                    'umri', 'bheempur', 'narnoor', 'khairdatwa', 'gundala', 'mahadapur', 'khampur', 'mahagaon', 'mankapur',
                    'gangapur', 'gunjala', 'tadihadapnur', 'balanpur', 'sonapur', 'nagolkonda', 'malepur', 'malangi'
                ],
                'Kerameri': [
                    'lakhmapur', 'kotha', 'parandoli', 'karanjiwada', 'anthapur', 'isapur', 'gouri', 'devadpalle',
                    'agarwada', 'keli buzurg', 'sangvi', 'keli khurd', 'bholepathur', 'sankaraguda', 'paraswada', 'anarpalle',
                    'devapur', 'kerameri', 'sakada', 'modi', 'khairi', 'surdapur', 'swarkheda', 'indapur', 'nishani',
                    'kothari', 'pipri', 'goyagaon', 'bheemangondi', 'dhanora', 'narsapur', 'parda', 'jhari', 'hatti',
                    'mettapipri', 'chintakarra', 'tukyanmovad', 'chalbordi', 'patnapur', 'babejheri', 'murikilanka', 'kallegaon',
                    'jodaghat'
                ],
                'wankdi': [
     'dhaba','sawathi', 'goagaon', 'chichpalle', 'gunjada', 'arli', 'bambara', 'sonapur', 'mahagaon', 'jambuldhari', 'lanjanveera',
    'wankdi khurd', 'neemgaon', 'akini', 'chavpanguda', 'navegaon', 'indhani', 'narlapur', 'wankdi kalan', 'khamana',
    'sarandi', 'khirdi', 'chincholi', 'ghatjangaon', 'tejapur', 'jaithpur', 'bendera', 'samela', 'borda', 'kanneragaon',
    'komatiguda', 'khedegaon', 'velgi', 'sarkepalle'
    ],

    'sirpur town' : [
    'makidi','jakkapur', 'hudkili', 'navegaon', 'venkatraopet', 'laxmipur', 'tonkini', 'parigaon', 'loanvelly', 'dhorpalle',
    'bhupalapatnam', 'sirpur', 'rudraram', 'cheelapalle', 'medpalle', 'garlapet', 'vempalle', 'achalli', 'chunchupalle',
    'chintakunta', 'heerapur', 'dabba', 'adepalle'
    ],

    'kouthala' : [
        'veervalli', 'sandgaon', 'pardi', 'tatipalle', 'veerdandi', 'bhalepalle', 'gundaipeta', 'thumbadihatti', 'ranvalli',
        'gudlabori', 'mogadagad', 'kumbari', 'muthampet', 'kouthala', 'talodi', 'nagepalle', 'babapur', 'ravindranagar',
        'gurudpeta', 'kanki', 'kannepalle', 'chipurudubba', 'babasagar', 'chintala manepalle', 'balaji ankoda', 'gangapur',
        'burepalle', 'korisini'
    ],

    'bejjur' : [
        'rebbena', 'rudrapur', 'munjampalle', 'karjavelli', 'kethini', 'dimda', 'chittam', 'gudem', 'buruguda', 'koyapalle',
        'nagepalle', 'mogavelly', 'shivapalle', 'ambhaghat', 'katepalle', 'pothepalle', 'marthadi', 'kukuda', 'rechini',
        'kushnepalle', 'gabbai', 'bejjur', 'chinnasiddapur', 'outsarangipalle', 'kondapalle', 'lodpalle', 'bombaiguda',
        'yelkapalle', 'yellur', 'penchikalpet', 'koyachichal', 'agarguda', 'gundepalle', 'papanpet', 'sushmeer', 'somini',
        'talai', 'muraliguda', 'kammergaon', 'nandigaon', 'jilleda'
    ],

    'kagaznagar' : [
        'malni', 'metindhani', 'marepalle', 'regulguda', 'kosni', 'boregaon', 'gondi', 'narapur', 'metpalle', 'dubbaguda',
        'ankusapur', 'nandiguda', 'vanjiri', 'bareguda', 'chinthaguda', 'easgaon', 'nazrulnagar', 'ankhoda', 'mandva',
        'gannaram', 'vallakonda', 'andavelli', 'bhatpalle', 'jagannathpur', 'bodepalle', 'boregaon', 'seetanagar', 'jambuga',
        'nagampet', 'mosam', 'raspalle', 'sarsala', 'kadamba', 'guntlapet', 'kagaznagar'
    ],

    'asifabad' : [
        'wadiguda', 'ada', 'danapur', 'ippalnavegaon', 'saleguda', 'govindapur', 'gundi', 'cherpalle', 'nandupa', 'rahapalle',
        'rajura', 'yellaram', 'kommuguda', 'dadpapur', 'khapri', 'babapur', 'ankusapur', 'buruguda', 'mothuguda', 'appepalle',
        'kommuguda', 'edulwada', 'singaraopet', 'chilatiguda', 'samela', 'tumpalle', 'dagleshwar', 'kosara', 'itukyal',
        'balegaon', 'demmidiguda', 'wavudham', 'mankapur', 'kutoda', 'malan gondi', 'ada dasnapur', 'wadigondi', 'mowad',
        'siryan mowad', 'balahanpur', 'temrianmovad', 'kowdianmovad', 'suddha ghat', 'devadurgam', 'chirrakunta', 'padibonda',
        'danaboinapeta', 'mondepalle', 'routsankepalle', 'perasnambal', 'addaghat', 'asifabad'
    ],

    'jainoor' : [
        'ashapalle', 'patnapur', 'gudamamda', 'addesar', 'bhusimatta', 'rasimatta', 'daboli', 'lendiguda', 'ushegaon',
        'shivanur', 'marlawai', 'dubbaguda', 'powerguda', 'jamni', 'polasa', 'jainoor'
    ],

    'utnoor' : [
        'chintakarra', 'narsapur buzurg', 'ghatti', 'wadoni', 'chandur', 'hasnapur', 'yenka', 'umri', 'sakhera', 'andholi',
        'pulimadgu', 'yenda', 'shampur', 'salewada buzurg', 'salewada khurd', 'kopergadh', 'wadgalpur khurd', 'tandra',
        'luxettipet', 'nagapur', 'ramlingampet', 'durgapur', 'rampur khurd', 'lakkaram', 'gangamapet', 'gangapur', 'kamnipet',
        'danthanpalle', 'ghanpur', 'narsapur new', 'bhupet', 'balampur', 'birsaipet', 'utnur'
    ],

    'ichoda' : [
        'adegaon khurd', 'gubba', 'junni', 'babuldhole', 'boregaon', 'kamgir', 'ponna', 'sunkidi', 'sirikonda', 'heerapur',
        'soanpalle', 'dhoba buzurg', 'talamadri', 'madapur', 'jamidi', 'adegaon buzurg', 'girjam', 'chincholi', 'navagaon',
        'dhaba khurd', 'salyada', 'malyal', 'mankapur', 'dharmapuri', 'jalda', 'kokasmannar', 'makhra buzurg', 'makhra khurd',
        'gundi', 'keshapatnam', 'narsapur', 'gundala', 'neradigonda', 'gaidpalle', 'gandiwagu', 'babjepet', 'jogipet',
        'sirichalma', 'narayanapur', 'neradigonda k', 'ichoda'
    ],

    'bazarhathnoor' : [
        'umarda buzurg', 'girjai', 'bhutai khurd', 'dhabadi', 'gokonda', 'yesapur', 'morekhandi', 'harkai', 'ananthapur',
        'dignoor', 'rampur', 'tembi', 'dharampuri', 'bhosra', 'dehgaon', 'chintal sangvi', 'bhutai buzurg', 'mankapur p',
        'jatarla', 'bazarhatnur', 'kolhari', 'balanpur', 'girnur', 'pipri', 'kandli', 'mohada', 'warthamanoor'
    ],

    'boath' : [
        'wajar', 'chintalabori', 'ghanpur', 'sonala', 'kowtha khurd', 'sangvi', 'kowtha buzurg', 'sakhera', 'tewiti', 'pardi buzurg',
        'pardi khurd', 'gollapur', 'babera', 'kantegaon', 'nigini', 'marlapalle', 'nakkalawada', 'karathwada', 'boath buzurg',
        'kangutta', 'pochera', 'kuchalapur', 'dhannur buzurg', 'pippaladhari', 'patnapur', 'narayanpur', 'anduru', 'dhannur khurd',
        'nagapur'
    ],
    
    'neradigonda': [
    'gajli', 'gandhari', 'kupti khurd', 'kumari', 'tejapur', 'chincholi', 'tarnam khurd', 'tarnam buzurg', 'madhapur',
    'kuntala buzurg', 'venkatapur', 'wagdhari', 'sowergaon', 'lokhampur', 'buddikonda', 'waddur', 'darba', 'bondadi',
    'surdapur', 'kishtapur', 'shankarapur', 'neradigonda', 'rolmanda', 'buggaram', 'kuntala khurd', 'nagamalyal',
    'peechra', 'boragaon', 'bandemregad', 'purushothampur', 'rajura', 'ispur', 'narayanapur', 'wankidi', 'koratkal buzurg',
    'dhonnora', 'koratkal khurd', 'lingatla', 'arepalle'
],
'sirpur': [
    'raghapur', 'bhurnur', 'phullara', 'devadpalle', 'seetagondi', 'pangdi', 'babjipet', 'chorpalle', 'vankamaddi', 'netnur',
    'pamulawada', 'sirpur', 'kohinur buzurg', 'kohinur khurd', 'shettihadapnur', 'chapri', 'dhanora', 'mahagaon',
    'ghumnur khurd', 'ghumnur buzurg', 'khanchanpalle', 'kothapalle', 'mamidipalle', 'lingapur', 'yellapatar', 'jamuldhara'
],
'rebbana': [
    'edvalli', 'khairgaon', 'navegaon', 'venkulam', 'rollapet', 'rampur', 'kondapalle', 'nerpalle', 'rebbana', 'gangapur',
    'passigaon', 'tungeda', 'pothpalle', 'dharmaram', 'nambal', 'gollet', 'sonapur', 'pulikunta', 'takkallapalle', 'rajaram',
    'rollapahad', 'seethanagar', 'komarvalli', 'rangapur', 'narayanpur', 'kistapur', 'jakkalpalle'
],
'bhimini': [
    'karjibheempur', 'akkalapalle', 'laxmipur', 'wadal', 'peddagudipet', 'surjapur', 'babapur', 'rajaram', 'peddapeta',
    'bhimini', 'bitturpalle', 'mallidi', 'venkatapur', 'gollaghat', 'veegaon', 'polampalle', 'shiknam', 'rampur', 'tekulapalle',
    'jankapur', 'yellaram', 'dampur', 'jajjarvelly', 'kothapalle', 'rebbena', 'veerapur', 'muthapur', 'kannepalle', 'metpalle'
],
'dahegaon': [
    'itial', 'gorregutta', 'borlakunta', 'keslapur', 'kothmir', 'beebra', 'pesarkunta', 'chedvai', 'ainam', 'polampalle',
    'thangallapalle', 'chinnagudipet', 'chinna thimmapur', 'pedda thimmapur', 'hathni', 'madavelli', 'saligaon', 'kalwada',
    'dahegaon', 'pambapur', 'kammarpalle', 'laggaon', 'bhogaram', 'vodduguda', 'brahmanchichal', 'bhamanagar', 'kunchavelli',
    'chandrapalle', 'etapalle', 'girvelli', 'chinnaraspalle', 'amargonda', 'loha', 'digida', 'teepergaon', 'rampur',
    'motlaguda', 'ravalpalle'
],
'vemanpalle': [
    'buyyaram', 'jilleda', 'jakkepalle', 'nagepalle', 'lingala', 'chintapudi', 'nagaram', 'suraram', 'bommena', 'chamanpalle',
    'baddampalle', 'dasnapur', 'kothapalle', 'vemanpalle', 'rajaram', 'sumputum', 'jajulpet', 'mukkidigudem', 'kallampalle',
    'gorlapalle', 'mamda', 'neelwai', 'kyathanpalle', 'mulkalpet', 'racherla'
],
'nennal': [
    'nennal', 'manneguda', 'konampet', 'kushenapalle', 'jangalpet', 'dammireddipet', 'kharji', 'gollapalle', 'nandulapalle',
    'ghanpur', 'jogapur', 'gundlasomaram', 'metpalle', 'mailaram', 'avadam', 'chittapur', 'gudipet', 'jhandavenkatapur',
    'chinavenkatapur', 'pottiyal', 'kothur'
],
'tandur': [
    'abbapur', 'narsapur', 'pegadapalle', 'repallewada', 'kothapalle', 'balhanpur', 'rechini', 'annaram', 'achalapur',
    'gampalpalle', 'chandrapalle', 'gopalnagar', 'kistampet', 'choutpalle', 'boyapalle', 'tandur', 'dwarakapur', 'kasipet',
    'katherla'
],
'tiryani': [
    'loddiguda', 'goena', 'dantanpalle', 'pangidimadra', 'ullipitadorli', 'lingiguda', 'devaiguda', 'boardham', 'areguda',
    'chopidi', 'jewni', 'goyagaon', 'dongargaon', 'koyatalandi', 'talandi', 'rallakamepalle', 'godelpalle', 'ginnedari',
    'sangapur', 'maindagudipet', 'tiryani', 'gangapur', 'gambhiraopet', 'duggapur', 'kannepalle', 'sonapur', 'edulpad',
    'dondla', 'irkapalle', 'chintapalle', 'mangi', 'rompalle', 'bheemapur', 'gundala', 'mankapur'
],
'jannaram': [
    'indhanpalle', 'kothapet', 'kawal', 'kishtapur', 'kamanpalle', 'raindlaguda', 'marriguda', 'murimadugu', 'venkatapur',
    'narsingapur', 'kalmadagu', 'dharmaram', 'badampalle', 'puttiguda', 'ponakal', 'jannaram', 'paidpalle', 'dongapalle',
    'bommena', 'papammaguda', 'chintaguda', 'malyal', 'singaraipet', 'thimmapur', 'rampur'
],
'kaddam peddur': [
    'gangapur', 'allampally', 'rampur', 'gandigopalpur', 'islampur', 'udumpur', 'dharmajipet', 'kalleda', 'laxmipur',
    'revajipet old', 'singapur', 'peddur', 'pandwapur', 'nawabpet', 'mallapur', 'bhuttapur', 'revojipet new', 'dasturabad',
    'ambaripet', 'kondkuru', 'kannapur', 'dharmaipet', 'narsapur', 'nachan yellapur', 'maddipadga', 'laxmisagar',
    'yelagadapa', 'masaipet', 'lingapur', 'sarangapur', 'dildarnagar', 'chittial', 'bellal', 'bhuthkur', 'munnial',
    'chennur', 'gondserial'
],
'sarangapur': [
    'potia', 'kupti', 'ponkur', 'pendaldhari', 'adelli', 'nagapur', 'jam', 'sarangpur', 'kowtla buzurg', 'jewly',
    'chincholi malak', 'kamkati', 'vaikuntapur', 'tandra', 'piyaramur', 'beervelli', 'vanjar', 'godsera', 'yakarpalle',
    'boregaon', 'dhani', 'alur', 'lakshmipur', 'chincholi buzurg', 'gopalpet', 'ranapur'
],
'kuntala': [
    'limba buzurg', 'medanpur', 'ambagaon', 'suryapur', 'downelle', 'burugupalle g', 'gulmadaga', 'ambakanti', 'kuntala',
    'oala', 'limba khurd', 'vittapur', 'venkur', 'penchikalpahad', 'andkur', 'bamini buzurg', 'nandan', 'turati', 'kallur',
    'mutakapalle', 'burgupalle k', 'arly khurd', 'dongargaon', 'chakepalle'
],
'kubeer': [
    'palsi', 'pardi khurd', 'jamgaon', 'ranjani', 'sirpalle', 'dodarna', 'belgaon', 'brahmeswar', 'marlagonda', 'veeragohan',
    'halda', 'shivani', 'chata', 'pardi buzurg', 'darkubeer', 'rajura', 'kubeer', 'khasra', 'chondi', 'jumda', 'sangvi',
    'kupti', 'varni', 'sonari', 'hampli buzurg', 'godapur', 'nighwa', 'mola', 'lingi', 'wai', 'sanwali', 'antharni',
    'malegaon', 'godsera', 'pangra', 'bakot', 'sowna'
],
'bhainsa': [
    'chichond', 'kumbhi', 'takli', 'linga', 'mirzapur', 'siddur', 'gundagaon', 'mahagaon', 'chintalabori', 'kotalgaon',
    'bijjur', 'sunkli', 'thimmapur', 'wanalpahad', 'ekgaon', 'babalgaon', 'pangri', 'manjri', 'sirala', 'elegaon',
    'badgaon', 'dahegaon', 'walegaon', 'kumsari', 'khatgaon', 'kamol', 'hasgul', 'mategaon', 'hampoli khurd',
    'boregaon buzurg', 'watoli', 'pendapalle', 'bhainsa'
],
'tanoor': [
    'wadjhari', 'beltaroda', 'bhosi', 'mahalingi', 'bamni', 'bondrat', 'bolsa', 'umri khurd', 'boregaon khurd', 'bember',
    'jhari buzurg', 'mugli', 'masalga', 'kupli', 'wadgaon', 'jewla khurd', 'kalyani', 'kolur', 'hipnally', 'elvi', 'hangirga',
    'dhagaon', 'singangam', 'doultabad', 'nandgam', 'tanoor', 'jewla buzurg', 'tondala', 'kharbala', 'yellawat', 'wadhone'
],
'mudhole': [
    'ramtek', 'machkal', 'mudgal', 'taroda', 'pipri', 'edbid', 'venkatapur', 'chinchala', 'vitholi', 'karegaon', 'chintakunta',
    'wadthala', 'boregaon', 'brahmangaon', 'ganora', 'riuvi', 'kirgul khurd', 'mudhole', 'takli', 'dhondapur', 'labdi',
    'bidralli', 'mailapur', 'ravindapur', 'basar', 'kirgul buzurg', 'voni', 'kowtha', 'ashta', 'surli', 'salapur', 'sawargaon'
],
'lokeswaram': [
    'potpalle m', 'hadgaon', 'sathgaon', 'biloli', 'hawarga', 'manmad', 'potpalle b', 'yeddur', 'rajura', 'gadchanda',
    'nagar', 'bhagapur', 'kistapur', 'puspur', 'lohesra', 'new raipur k r c', 'joharpur', 'kankapur', 'wastapur', 'watoli',
    'dharmara', 'panchgudi', 'mohalla', 'bamni k'
],
'dilawarpur': [
    'anjani', 'kurli', 'kadili', 'malegaon', 'kalva', 'new lolam r c', 'daryapur', 'narsapur', 'naseerabad', 'rampur',
    'cherlapalle', 'temborni', 'samanderpalle', 'gundampalle', 'dilawarpur', 'sirgapur', 'mayapur', 'banaspalle',
    'lingampalle', 'kanjar', 'ratnapur k', 'sangvi', 'mallapur', 'velmel'
],
'nirmal': [
    'vengvapet', 'dyangapur', 'yellareddipet', 'medpalle', 'neelaipet', 'ananthpet', 'langdapur', 'talwada', 'chityal',
    'new mujgi', 'thamsa', 'yellapalle', 'bhagyanagar', 'new pochampad', 'ratnapur kondli', 'kondapur', 'akkapur',
    'muktapur', 'shakari', 'kadthal', 'koutla k', 'siddankunta new', 'old pochampad', 'pakpatla', 'madhapur', 'jafrapur',
    'ganjal', 'soan', 'nirmal'
],
'laxmanchanda': [
    'waddyal', 'kankapur', 'narsapur', 'boregaon', 'kanjar', 'babapur', 'potapalle k', 'thirpalle', 'laxmanchanda',
    'peechara', 'new velmal', 'sangampet', 'new bopparam', 'kuchanpalle', 'dharmaram', 'parpalle', 'potpalle b', 'mallapur',
    'machapur', 'munipalle', 'chamanpalle', 'chintalchanda'
],
'mamda': [
    'pulimadugu', 'tandra', 'vasthapur', 'rampur', 'rasimatla', 'gayadpalle', 'burugupalle', 'kishanraopet', 'parimandal',
    'arepalle', 'lingapur', 'raidhari', 'kappanpalle', 'dimmadurthy', 'kotha sangvi r c', 'mamda', 'kotha lingampalle r c',
    'koratikal', 'chandaram', 'bandal khanapur', 'potharam', 'ananthpet', 'kotha timbareni r c', 'adarsanagar r c kothur edudur',
    'kamal kote', 'ponkal', 'naldurthi', 'venkatapur'
],
'khanapur': [
    'paspula', 'itikyal', 'gummanuyenglapur', 'dhomdari', 'vaspalle', 'shetpalle', 'kosagutta', 'pembi', 'venkampochampad',
    'burugpalle', 'bevapur r', 'rajura', 'mandapalle', 'ervachintal', 'chamanpalle', 'beernandi', 'advisarangapur', 'nagpur',
    'iqbalpur', 'tarlapad', 'sathnapalle', 'patha yellapur', 'kothapet', 'dilwarpur', 'bavapur k', 'khanapur', 'badankurthy',
    'maskapur', 'surjapur', 'medampalle', 'thimmapur'
],
'dandepalle': [
    'gurrevu', 'allipur', 'nagasamudram', 'tallapet', 'makulpet', 'mamidipalle', 'kundelapahad', 'tanimadugu', 'dandepalle',
    'medaripet', 'lingapur', 'bikkanguda', 'laxmikantapur', 'dwaraka', 'peddapet', 'dharmaraopet', 'narsapur', 'venkatapur',
    'chintapalle', 'karvichelma', 'mutyampet', 'rebbenpalle', 'kondapur', 'kasipet', 'velganoor', 'jaidapet', 'nambal',
    'gudam', 'kamepalle'
],
'kasipet': [
    'kurreghad', 'sonapur', 'venkatapur', 'tirmalapur', 'dharmaraopet', 'malkepalle', 'rottepalle', 'peddapur', 'gatrapalle',
    'chintaguda', 'kondapur', 'konur', 'pallamguda', 'kankalapur', 'kometichenu', 'gurvapur', 'muthempalle', 'varipet',
    'devapur', 'kasipet'
],
'bellampalle': [
    'ankusam', 'chakepalle', 'chandravelli', 'rangapet', 'dugnepalle', 'akenipalle', 'batwanpalle', 'perkapalle',
    'bellampalle part'
],
'kotapalle': [
    'nakkalpalle', 'brahmanpalle', 'mallampet', 'shankarpur', 'shetpalle', 'pangadisomaram', 'kotapalle', 'vesonvai',
    'sarvaipet', 'kondampet', 'nagampet', 'bopparam', 'venchapalle', 'supak', 'jangaon', 'algaon', 'pullagaon', 'sirsa',
    'edula bandam', 'lingannapet', 'edagatta', 'pinnaram', 'parpalle', 'yerraipet', 'borampalle', 'kawarkothapalle', 'annaram',
    'arjungutta', 'rajaram', 'rampur', 'kollur', 'dewalwada', 'rapanpalle'
],
'mandamarri': [
    'andgulapet', 'chirrakunta', 'sarangapalle', 'thimmapur', 'amerwadi', 'venkatapur', 'ponnaram', 'mamidighat', 'kyathampalle',
    'mandamarri'
],
'luxettipet': [
    'talamalla', 'challampet', 'balraopet', 'jendavenkatapur', 'rangapet', 'chandram', 'venkataraopet', 'ellaram', 'kothur',
    'utukur', 'modela', 'itkyal', 'lingapur', 'thimmapur', 'laxmipur', 'pothepalle', 'gullakota', 'mittapally', 'luxettipet'
],
'mancherial': [
    'ryali', 'nagaram', 'gadhpur', 'gudipet', 'subbapalle', 'peddampet', 'kondapur', 'donabanda', 'padthenpalle', 'karnamamidi',
    'kondepalle', 'rapalle', 'hajipur', 'narsingapur', 'namnur', 'chandanapur', 'mulkalla', 'kothapalle', 'vempalle',
    'teegalpahad', 'naspur', 'thallapalle', 'singapur', 'mancherial'
],
'jaipur': [
    'kankur', 'mittapalle', 'reddipalle', 'dampur', 'burugupalle', 'pothanpalle', 'bhimaram', 'ankushapur', 'polampalle', 'jaipur',
    'narva', 'maddikunta', 'ramaraopet', 'indaram', 'tekumatla', 'shetpalle', 'yelkanti', 'pegadapalle', 'gangipalle',
    'narasingapuram', 'bejjal', 'maddulapalle', 'kundaram', 'arepalle', 'rommipur', 'kistapur', 'maddikal', 'kothapalle',
    'velal', 'gopalpur', 'pownur', 'shivvaram'
],
'chennur': [
    'buddaram', 'sankaram', 'kannepalle', 'shivalingapur', 'akkapalle', 'chintapalle', 'yellakkapet', 'kistampet',
    'khambojipet', 'lingampalle', 'suddal', 'bhamraopet', 'kathersala', 'narayanpur', 'dugnepalle', 'raipet', 'angarajpalle',
    'kachanpalle', 'gangaram', 'asnad', 'kommera', 'sundersala', 'narasakkapet', 'pokkur', 'chakepalle', 'ponnaram',
    'somanpalle', 'nagapur', 'beervelli', 'chennur'
] 
            }
        }

        # Populate Rajasthan data
        rajasthan, created = State.objects.get_or_create(name='Rajasthan')
        self.add_districts(rajasthan, rajasthan_data)

        # Populate Andhra Pradesh data
        andhra_pradesh, created = State.objects.get_or_create(name='Andhra Pradesh')
        self.add_districts(andhra_pradesh, andhra_pradesh_data)

        self.stdout.write(self.style.SUCCESS('Successfully populated the RDS instance with location data.'))
