from django.core.management.base import BaseCommand
from gee_api.models import State, District, SubDistrict, Village
from typing import List, Dict, Tuple, Union


class Command(BaseCommand):
    help = 'Populate the RDS instance with location data for states, districts, sub-districts, and villages'

    def add_villages(self, subdistrict: SubDistrict, villages: List[Union[str, Tuple[str, int]]]) -> None:
        """
        Adds villages to a given subdistrict.

        Args:
            subdistrict (SubDistrict): The subdistrict to which the villages belong.
            villages (List[Union[str, Tuple[str, int]]]): A list of village names or (name, id) tuples.
        """
        for village_item in villages:
            if isinstance(village_item, tuple):
                village_name, village_id = village_item
                village, created = Village.objects.get_or_create(
                    name=village_name, 
                    subdistrict=subdistrict,
                    defaults={'village_id': village_id}
                )
                # Update the village_id if the village already exists
                if not created and village.village_id != village_id:
                    village.village_id = village_id
                    village.save()
            else:
                # For backward compatibility with old format (only village name)
                Village.objects.get_or_create(name=village_item, subdistrict=subdistrict)
                
        self.stdout.write(self.style.SUCCESS(f'Added villages to {subdistrict.name}'))

    def add_subdistricts(self, district: District, subdistricts_and_villages: Dict[str, List[Union[str, Tuple[str, int]]]]) -> None:
        """
        Adds subdistricts and their corresponding villages to a given district.

        Args:
            district (District): The district to which the subdistricts belong.
            subdistricts_and_villages (Dict[str, List[Union[str, Tuple[str, int]]]]): A dictionary where the keys are subdistrict names
                                                             and the values are lists of village names or (name, id) tuples.
        """
        for subdistrict_name, villages in subdistricts_and_villages.items():
            subdistrict, created = SubDistrict.objects.get_or_create(name=subdistrict_name, district=district)
            self.add_villages(subdistrict, villages)
        self.stdout.write(self.style.SUCCESS(f'Added subdistricts to {district.name}'))

    def add_districts(self, state: State, districts_and_subdistricts: Dict[str, Dict[str, List[Union[str, Tuple[str, int]]]]]) -> None:
        """
        Adds districts and their corresponding subdistricts to a given state.

        Args:
            state (State): The state to which the districts belong.
            districts_and_subdistricts (Dict[str, Dict[str, List[Union[str, Tuple[str, int]]]]]): A dictionary where the keys are district names,
                                                                          the values are dictionaries that map subdistrict
                                                                          names to lists of village names or (name, id) tuples.
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

        # New data for Karnataka
        karnataka_data = {
            'Raichur': {
                'Lingsugur': ['upanhal', 'ankanhal', 'tondihal', 'halkawatgi', 'palgal dinni', 'tumbalgaddi', 'rampur', 'nagarhal', 'bhogapur', 'baiyapur', 'khairwadgi', 'bandisunkapur', 'bommanhal', 'sajjalagudda', 'komnur', 'lukkihal big', 
'lukkihal small', 'uppar nandihal', 'killar hatti', 'ashihal', 'advibhavi mudgal', 'kannapur hatti', 'mudgal rural', 'jantapur', 'yerdihal khurd', 'yerdihal big', 'amdihal', 'bellihal', 'kansavi', 'adapur', 
'komlapur', 'ramatnal', 'byalihal', 'wandali', 'turadgi', 'arya bhogapur', 'hunoor', 'makapur', 'talekat', 'marli', 'bannigol', 'piklihal', 'ulimeshwar', 'vyakarnhal', 'nagalapur', 'heggapur', 'chattar', 'todki', 
'kumarkhed', 'nowli', 'kamaldinni', 'chittapur', 'jawoor small', 'jawoor big', 'roudal banda', 'jungi rampur', 'upperi small', 'sunkal', 'halbhavi', 'gorebal', 'yargunti', 'upperi big', 'toral benchi', 'nandihal', 
'bendona', 'narakaladinni', 'julgudda', 'hanumangudda hosur', 'anahosur', 'eachanhal', 'kesarhatti', 'jalibenchi', 'mincheri', 'kalapur', 'aidanhal', 'yalagaladinni', 'karadakal', 'adavibhavi', 'neeralkera', 
'margatnal', 'chitranhal', 'gundasagar', 'kachapur', 'mavinbhavi', 'bhupur', 'rampur', 'kallilingsugur', 'hunkunti', 'kuppigudda', 'sarjapur', 'gonwar', 'amarawati', 'basapur', 'hoovinabhavi', 'buddinni', 'sanbal', 
'jaldurga', 'yalgundi', 'yaragudi', 'kadadargaddi', 'hanchinal', 'shilahalli', 'gonwatla', 'guntagola', 'ramalooti', 'aidbhavi', 'tanmankal', 'raidurga', 'gadgi', 'pai doddi', 'golpalli', 'yarjanti', 'bandebhavi', 
'hosagudda', 'benchaldoddi', 'gurgunta', 'paramapur', 'devar bhupur', 'yaradona', 'phoolabhavi', 'honnahalli', 'gudadanhal', 'medinapur', 'kotha', 'goudur', 'machanur', 'yalaghatta', 'kaddona', 'tawag', 'roudala banda', 
'mallapur', 'hosur', 'anwari', 'hire nagnur', 'chikka nagnur', 'veerapur', 'nilogal', 'chukanahatti', 'gejjelagatta', 'hire hesarur', 'chick hesarur', 'kadadarahal', 'teribhavi', 'buddinni', 'gudihal', 'mattur', 
'kunikellur', 'mittikellur', 'sante kellur', 'muslikarlkunti', 'bendarkarlkunti', 'ankusadoddi', 'mudwal', 'katagal', 'uskihal', 'dabbermadu', 'maraldinni', 'mudaldinni', 'sultanpur', 'jakker madu', 'vyasa nandihal', 
'kannal', 'timmapur', 'tirthabhavi', 'dignaikanbhavi', 'nirlooti', 'advibhavi maski', 'benkanhal', 'belladamaradi', 'venkatapur', 'maski', 'naraga benchi', 'antargangi big', 'myadarnal', 'medikinhal', 'bailgudda', 
'hadagali', 'desai bhogapur', 'yerdoddi', 'baggalgudda', 'kamandaldinni', 'talekhan', 'hatti', 'mudgal', 'lingsugur', 'hatti gold mines'],
                
                
                'Devadurga': ['veergot', 'bunkaldoddi', 'chinchodi', 'lingadhalli', 'mudgot', 'bagur', 'herundi', 'navilgudda',
                              'jambaldinni', 'medinapur', 'jalhalli', 'yergudda', 'bassapur', 'hosur siddapur', 'bommanhalli',
                              'parapur', 'karadigudda', 'amrapur', 'suladgud', 'mandalgud', 'gajaldinni', 'mukanhal', 'mundargi', 
                              'ganajali', 'devatgal', 'katmalli', 'huligud', 'kakkaldoddi', 'kamaldinni', 'mykaldoddi', 'bhogiramangund', 
                              'somanmardi', 'gandhal', 'ooti', 'wandli', 'palkanmardi', 'madarkal', 'devergud', 'mudalagund', 'sunnadkal', 
                              'galag', 'chadkalgudda', 'anchesugur', 'gopalpur', 'wagadambli', 'huvinhadgi', 'joladhadgi', 'dondambli', 'benkal',
                              'konchapli', 'mydargol', 'karkihalli', 'paratpur', 'kopper', 'kurkihalli', 'yatgal', 'herur', 'salkyapur', 
                              'gopendeverhalli', 'nagarhal', 'chickbudur', 'arshangi', 'ramanhal', 'hunur', 'hemnhal', 'nagargund', 
                              'anjal', 'nilvanji', 'karegud', 'venglapur', 'samudra', 'nimbaidoddi', 'guddad irabgera', 'kelgin irabgera', 
                              'mansagal', 'kotigud', 'sasvigera', 'kardigudda', 'gundgurthi', 'sugarhal', 'jerbandi', 'kamdhal', 'devergud',
                              'yermasal', 'chickhonkuni', 'miyapur', 'masarkal', 'guntarhal', 'matpalli', 'itagi', 'gagal', 'gugal', 'chickraikumpi', 
                              'hireraikumpi', 'madarkal', 'apprahal', 'baswantpur', 'hemanal', 'bommanhal', 'kolur', 'shavantgera', 'masihal', 
                              'hirebudur', 'budinhal', 'hanchinhal', 'hirekudalgi', 'chickkudalgi', 'honnatagi', 'khanapur', 'amrapur', 
                              'ingaladhal', 'haddinhal', 'sunkeshwarhal', 'kakkargal', 'aldharti', 'khardigud', 'ramdurg', 'maladkal', 'gabbur',
                              'maseedpur', 'ganekal', 'neelgal', 'pandyan', 'kachapur', 'kothdoddi', 'chikkaldoddi', 'yeldoddi', 'hemnur', 'teggihal',
                              'chintalkunta', 'shakapur', 'jinnapur', 'govindpalli', 'hungunbad', 'gajjibhavi', 'mustoor', 'shivangi', 'jaradbandi',
                              'honkatmalli', 'kardona', 'malkamdinni', 'mallinaikandoddi', 'piligund', 'hal jadaldinni', 'arkera', 'benderganekal',
                              'mallapur', 'bhumangund', 'adkalgud', 'anwar', 'akalkumpi', 'shavantgal', 'alkod', 'kyadigera', 'malledevergud', 
                              'bandegud', 'jutmardi', 'nagoli', 'buddinni', 'jagatkal', 'agrahar', 'rekalmardi', 'markamdinni', 'jagir jadaldinni',
                              'yermarus', 'heggaddinni', 'nagaddinni', 'tippaldinni', 'devadurga'],
                'Raichur' : [ 'arshanagi', 'gurjapur', 'timmapur g', 'hanmapur', 'hemberhal', 'meerapur', 'timmapur h', 'srinivaspur', 
                              'bevin benchi', 'kadlur', 'karekal', 'rangapur', 'yedlapur', 'nagalapur', 'hegsanhalli', 'deosugur', 
                               'wadloor', 'hanumandoddi', 'ganjhalli', 'ibrahimdoddi', 'korvihal', 'korthkunda', 'mamadadoddi', 
                               'yergunta', 'sagamkunta', 'kadlur', 'madmandoddi', 'raldoddi', 'waddepalli', 'dongarampur', 'korvakhurd', 
'agrahar', 'korvakala', 'budidipad', 'kurtipli', 'athkur', 'gajral', 'yapaldinni', 'appandoddi', 
'kothdoddi', 'palwaldoddi', 'nagandoddi', 'ganmur', 'shakwadi', 'polkamdoddi', 'katlatkur', 
'kadgamdoddi', 'chandrabanda', 'arsigera', 'wadlamdoddi', 'mandalgera', 'singnodi', 'yegnur', 
'sanknur', 'kurabdoddi', 'wadwati', 'baidoddi', 'ghousenagar', 'bolmandoddi', 'sidrampur', 
'maliabad', 'mittimalkapur', 'bijangera', 'devanpalli', 'rajalbanda', 'ayazpur', 'bapur', 
'undral doddi', 'mallapur', 'jegarkal', 'chicksugur', 'kuknoor', 'manslapur', 'merched', 'hospet', 
'arlappanahuda', 'raghunathanhalli', 'sultanpur', 'murhanpur', 'halvenktapur', 'kalmala', 
'j venktapur', 'fathepur', 'gonhal', 'hunsihalhuda', 'mamdapur', 'nelhal', 'pesaldinni', 
'merchathal', 'asapur', 'arlibenchi', 'jalibenchi', 'dinni', 'garaldinni', 'khanapur', 'udamgal', 
'kamlapur', 'anwar', 'gonwar', 'tuntapur', 'murkidoddi', 'masdoddi', 'julamgera', 'lingankhan doddi', 
'jambaldinni', 'mallapur', 'yergera', 'manjerla', 'gadhar', 'naglapur', 'purtipali', 'alkur', 'godihal', 
'upral', 'gunjhalli', 'midgaldinni', 'puchaldinni', 'kannedoddi', 'kothdoddi', 'maldoddi', 
'matmari', 'moodaldinni', 'heerapur', 'gatbichal', 'kataknur', 'hanmapur', 'bichal', 'yedlapur', 
'turkandona', 'dugnoor', 'karebudur', 'hanchinhal', 'gandhal', 'gillesugur', 'tungabhadra', 'bullapur', 
'chickmanchal', 'gunderveli', 'buddinni', 'naddigaddimalkapur', 'gangwar', 'idapnur', 'meerapur', 
'mirzapur', 'talmari', 'shaktinagar', 'raichur'
],
                'Manvi' : ['yatgal', 'kachapur', 'eklasapur', 'watgal', 'nelkola', 'ameengad', 'kotekal', 'pamankallur', 'anandgal', 'harvapur', 'tupdoor', 'benchamardi', 'hilalpur', 'gudihal', 'chilkaragi', 'irkal', 'basapur', 'parasapur', 
'joladarasi', 'jangamarhalli', 'yeddal dinni', 'm ramaldinni', 'halapur', 'nagaldinni', 'hire kadboor', 'jinnapur', 's ramal dinni', 'kabberhal', 'hanchanhal', 'tuggal dinni', 'toran dinni', 'goge hebbal', 
'chikkadinni', 'malkapur', 'markamdinni', 'sunknoor', 'hiredinni', 'malladgudda', 'donamaradi', 'chincharaki', 'huda', 'bomsandoddi', 'kasan doddi', 'donmardi', 'heera', 'buddinni', 'toppal doddi', 'timmapur', 
'hussainpur', 'saidapur', 'u gud dinni', 'kowtal', 'hire hanagi', 'chikka hanagi', 'potapur', 'goldinni', 'chikkabadardinni', 'dewatgal', 'bullapur', 'kalamgere', 'kurkunda', 'wadwatti', 'patakam doddi', 'malat', 
'narabanda', 'hunched', 'murkigudda', 'marata', 'nawalkal', 'nugdoni', 'ballatgi', 'hire badardinni', 'bagalwad', 'nakkunda', 'gavigat', 'aldhal', 'sirwar', 'jakkal dinni', 'atnur', 'shakapur', 'singaddinni', 
'ganadinni', 'jalapur', 'kadadinni', 'jambaldinni', 'chagbhavi', 'gud dinni k', 'sangapur', 'sannahosur', 'lakkam dinni', 'halli', 'madagiri', 'machnur', 'kallur', 'hokrani', 'bommanahal', 'bevinur', 'tupdur k', 
'harvi', 'kardigud', 'mallige madugu', 'naslapur', 'chimlapur', 'govinadoddi', 'neermanvi', 'kapgal', 'bettadur', 'bailmarchad', 'kurdi', 'aroli', 'advi khanapur', 'walkam dinni', 'kambalanetti', 'gorkal', 
'sunkeswara', 'sadapur', 'murharpur', 'seekal', 'bapur', 'korvi', 'pannuru', 'arnalli', 'rajalbanda', 'tammapur', 'jukur', 'rajoli', 'nandihal', 'manvi r', 'rabbankal', 'daddal', 'katarki', 'madlapur', 'burhanpur', 
'buddinni', 'rangdhal', 'mustoor', 'yarmal doddi', 'rajaldinni', 'jutlapur', 'hosur umli', 'chikkotankal', 'nalgamdinni', 'pannur jagir', 'chikalparvi', 'yedival', 'badlapur', 'belwat', 'utaknur', 'dhotarbandi', 
'udbal', 'tadkal', 'byagwat', 'jeenur', 'potanhal', 'karegudda', 'janekal', 'amarawati', 'bhogawati', 'hire kotankal', 'muddamgaddi', 'kharabadinni', 'eralgaddi', 'devipur', 'manvi']
,
                'Sindhnur' : ['mahampur', 'bommanahal u', 'ratanapur', 'sankanhal', 'gunda', 'hogernhal', 'gudihal', 'gadratigi',
                              'hattigudda', 'hirebhergi', 'bhogapur', 'mullur u', 'virapur', 'kardchalami', 'gorloti', 'umloti', 'bukanhatti',
                              'chikbhergi', 'turvihal', 'kalmangi', 'hosshalli k', 'jambunathanahalli', 'bassapur k', 'gandhinagar', 'hanumapur',
                              'hanchinhal k', 'jalihal', 'hokarani', 'bagalapur', 'boppur', 'kaniganhalu', 'matur', 'uppaldoddi umli', 'tidgol', 
                              'nedigol', 'kurukunda', 'gunjanalli', 'virapapur', 'arlihalli', 'sunkanur', 'chikkkadbur', 'kyathanahatti', 'udbal umli',
                              'deensamudra', 'hasamakal', 'gudadur', 'parapura', 'merinahal', 'nanjaldinni', 'hanpanhal', 'gudgaldinni', 'hanchinhal u',
                              'kanoor', 'hedigibal', 'gonhal', 'rangapur', 'muddapur', 'kholabal', 'harapur', 'yelekudalgi', 'chiratanal', 'bommanhal ej',
                              'devergudi', 'bassapur ej', 'kunnatgi', 'pagadadinni', 'tippanhatti', 'mullur', 'kallur', 'butaldinni', 'mallapur', 'hullur',
                              'balganur', 'goudanbhavi', 'govindnaikandoddi', 'belliganur', 'buddinni', 'jalwadgi', 'diddigi', 'jangamerhatti a',
                              'sivajawalgera', 'amarapur khadehola d', 'sultanpur', 'jawalgera', 'turakatti d', 'maldinni khadehola', 'kanakraddi khadehola',
                              'ramathanhal', 'banniganur', 'yapalparvi', 'walkamdinni', 'timmapur', 'ragalparvi', 'puldinni', 'dumti', 'gonwar', 
                              'hulgunchi', 'ayyanur', 'chintamandoddi', 'chitrali', 'pulmeswardinni', 'hedginhal', 'yeddaldoddi', 'giniwar', 
                              'walbellary', 'udbal jagir', 'gomarsi', 'madsirwar', 'belgurki', 'kannari', 'maldinni', 'alabanoor', 'haretnur', 'badarli', 'gonniganoor', 'uppal', 'hosalapur', 'sindhnur rural', 'sashalli', 'hosshalli ej', 'amarapur', 'budiwal', 'somlapur', 'salgunda', 'dhadesugur', 'bassapur d', 'kengal', 'hatti', 'gorebal', 'sasalmari', 'malakapur', 'konthanur', 'channahalli', 'siddrampur', 'mavinmadu', 'roudkunda', 'gobberkal', 'huda', 'mukunda', 'singapur', 'sindhnur'
                             ],
                
            }
        }
        
        uttar_pradesh_data = {
            'Chitrakoot' : {
                'Mau' : ['majhgawan mustakil', 'bhambhet mustkil', 'ragauli mustkil', 'parakon', 'khatawara', 'malawara', 'nadin kurmiyan', 
                         'choraha', 'binaura', 'paikora', 'karaundi kalan', 'kuin', 'ram tekawa', 'ghurehta', 'amarpur', 'singhpur', 'kapuri', 
                         'rithi mustakil', 'rupauli mustkil', 'tir mau mustkil', 'bhadevra', 'amawan', 'aman', 'sikari', 'piyariya khurd',
                         'piyariya mafi', 'chhibon', 'khajuriha khurd', 'nonmai', 'chahata', 'atarsui', 'gobraul', 'baruwa mustkil', 
                         'sirwal mafi mustkil', 'balhaura', 'naudhiya mustkil', 'silauta mustkil', 'kataiya khadar mustkil', 'barachhi mustkil',
                         'suhel mustkil', 'chandaha', 'hanna binaika', 'piyariya kalan', 'piparaund', 'chak bhadesar', 'dhadhawar', 'dhawada', 
                         'khajuriha kalan', 'bhakharwar', 'pahadi', 'lodhaura barethi', 'ram nagar', 'basingha', 'dadhiya', 'rehi', 'reruwa', 
                         'budhawal', 'rewadi', 'ufarauli', 'bariya', 'turka viran', 'bandhi', 'lamakol', 'rampur', 'bisaundha', 'ghunuwa',
                         'deundha', 'itwan', 'khor', 'lauri', 'chakaur mustkil', 'redi bhusauli mustkil', 'basrehi mustkil', 'biyawal mustkil',
                         'chak alaiya', 'tadi mustkil', 'dubari', 'sakhaunha', 'sikraun', 'konpa', 'barwar mustkil', 'mawai kalan mustkil',
                         'mandaur', 'bambura', 'mau mustkil', 'ahiri', 'suraundha', 'rataura', 'sesa subakara mustkil', 'patori', 'dadari', 
                         'hatawa', 'pura', 'karahi', 'jorwara', 'itaha devipur', 'mawai khurd', 'chak mawai radha', 'tenduwa mafi',
                         'khandevra mafi', 'deora', 'khandokhar', 'nevhra', 'khandeha', 'jafarpur', 'mohini', 'bihata', 'chitawar', 'tatwar', 
                         'nibi', 'manodhasani', 'khapatiha', 'aunjhar', 'bamburi', 'bhitari', 'tilauli mustakil', 'chhiolaha', 'man kunwar mustakil', 
                         'tikara', 'pashchim palai mustakil', 'purab palai mustakil', 'kotara khambha', 'gadhawa', 'bariyari kalan mustakil', 
                         'bariyari khurd mustakil', 'barha kotra mustakil', 'benipur pali mustakil', 'pardawan mustakil', 'kalchiha', 'mahraja',
                         'arawari naudhiya', 'muraka', 'kandhara', 'karaundi khurd', 'obari', 'bojh', 'bhatgawan', 'channadh', 'lalai', 
                         'haradi kalan', 'lodhauta khurd', 'lodhauta kalan', 'hardi khurd', 'atari majara', 'goiya kalan', 'khohar', 'turgawan',
                         'madaha', 'goiya khurd', 'bargadh', 'usari mafi', 'chharehra', 'chhataini mafi', 'manka chhataini', 'chachokhar', 
                         'jamira', 'koniya', 'semara', 'kol majara', 'kaniyadh', 'dondiya mafi', 'kotwa mafi', 'gahur', 'kataiya dandi',
                         'raipura', 'dubi', 'lapaon', 'rajapur']
            }
        }
        
        maharashtra_data = {
            'Nashik' : {
                'surgana' : [
                    'bardipada', 'chinchale', 'chandrapur', 'hadkaichond', 'gondune', 'ranjune', 'kukudne', 'deshmukh nagar', 'songir', 
                    'udmal', 'deogaon', 'pangarne', 'wangan', 'pimpalsond', 'malgonde', 'khuntavihir', 'mohapada', 'ranvihir', 'galbari', 
                    'karanjul kelwan', 'chinchpada', 'sundarban', 'raghatvihir', 'fanaspada n v', 'mandha', 'guhijambhulpada', 'rasha', 'borchond n v', 
                    'nimbarpada', 'umbarthan', 'subhashnagar', 'dolhare', 'amzar', 'satkhamb', 'ambatha', 'kothule', 'krishnanagar n v', 'gopalnagar n v',
                    'kathipada', 'dodichapada', 'torandongri', 'baflun', 'mhaiskhadak', 'udaldari', 'karanjul surgana', 'vijaynagar', 'shrirampur', 'devaldari',
                    'walutzira', 'bhavandagad', 'bhadar', 'nawapur', 'umbarpada', 'bhormal', 'umbarvihir n v', 'palvihir', 'khokari', 'jamunmatha n v',
                    'wadpada', 'karanjali', 'talpada', 'karwande', 'durgapur', 'chinchpada', 'ladgaon', 'bubli', 'umaremal', 'malgavhan', 'udaypur',
                    'garmal', 'suryagad', 'pratapgad', 'alangun', 'hatrundi', 'patali', 'payarpada', 'umbarde', 'ganeshnagar', 'hanumantmal', 'ahmadgavhan',
                    'bival', 'vadmal', 'mani', 'khobala mani', 'palsan', 'palashet', 'merdand', 'khadakmal', 'deola', 'kukudmunda', 'morchonda', 'umbarde m', 
                    'shribhuvan', 'mothamal', 'hatgad', 'sajole', 'pohali', 'nagshewadi', 'vanjulpada', 'hatti bk', 'chirai', 'mohapada', 'roti', 'ghodambe',
                    'borgaon', 'hiradipada', 'chikhali', 'sarad', 'ghagbari', 'kharude', 'umbarpada digar', 'sanjaynagar', 'harantekadi', 'shinde', 'waghdhond', 
                    'sabardara', 'bhintghar', 'malegaon', 'salbhoye', 'chikadi', 'pilukpada', 'rokadpada', 'dangrale', 'rahude', 'sule', 'wangan sule', 'amdapalsan',
                    'awalpada', 'bendwal', 'bhawada', 'rakshasbhuvan', 'karanjul', 'amdabarhe', 'dudhawal', 'gahale', 'kahandolsa', 'waghadi', 'kotamba',
                    'pimpalchond', 'vaghanakhi', 'mahismal', 'galwad', 'ronghane', 'nadagdari', 'wadpada', 'murumdari', 'sadudne', 'bhatvihir', 'mankhed', 
                    'jambhulpada', 'bijurpada', 'sambarkhal', 'gadga', 'hatti b', 'gopalpur', 'gurtembhi', 'thangaon', 'bedse', 'ambode', 'mandve', 'sarmal', 
                    'undohal', 'khadki digar', 'kelavan', 'bhenshet', 'khobale digar', 'kahandolpada', 'bhati', 'khirdi', 'khokarvihir', 'zagadpada', 'ambupada',
                    'kotambi', 'modhalpada', 'khirman', 'kalmane', 'barhe', 'alivdand', 'bhegu', 'sayalpada', 'wanganpada', 'haste', 'ambepada', 'jahule', 'suktale',
                    'tapupada', 'hemadpada', 'masteman', 'mangdhe', 'warambhe', 'surgana'
                ]
            },
            
            'Aurangabad' : {
                'Paithan' : [
                    'shekta', 'gadhegaon paithan', 'tondoli', 'jainpur', 'kaudgaon', 'nandalgaon', 'taherpur', 'dhupkheda', 'dinnapur', 'chauryahattar jalgaon',
                    'shahapur manegaon', 'khamjalgaon', 'lohagaon bk', 'lohagaon kh', 'bramhagavhan', 'mavasgavhan', 'lamgavhan', 'jogeshwari', 'mulani wadgaon',
                    'shevata', 'balapur', 'mankapur', 'dhakephal', 'amrapur', 'taru pimpalwadi', 'hanumantgaon', 'naigavhan', 'khandewadi', 'kesapuri',
                    'babhulgaon', 'pangra', 'bokud jalgaon', 'patode wadgaon', 'meharban naik tanda', 'jambhali', 'chincholi', 'shivani', 'farola', 'mharola', 
                    'jaitpur', 'paithan kheda', 'waki', 'imampur', 'godhegaon gangapur', 'ballalpur', 'ranjangaon khuri', 'ranjani', 'bangala tanda', 'banni tanda',
                    'bidkin', 'krishnapur', 'nilajgaon', 'wadgavhan', 'sompuri', 'gidhada', 'aliyabad', 'padli', 'dongri naik tanda', 'warwandi kh', 'porgaon tanda',
                    'porgaon', 'gazipur', 'lakhegaon', 'alipur', 'georai bashi', 'dongaon', 'tekadi tanda', 'daregaon', 'balanagar', 'kapuswadi', 'karkin',
                    'dhorkin', 'wadala', 'wawa', 'kasarpadli', 'warudi bk', 'dhangaon', 'takli paithan', 'borgaon', 'isarwadi', 'wahegaon', 'pachalgaon', 
                    'diyanatpur', 'narayangaon', 'muradabad', 'gharegaon', 'ektuni', 'hirapur', 'thapati tanda', 'rajapur', 'adool kh', 'georai kh', 'georai bk',
                    'honobachiwadi', 'abdullapur', 'adool bk', 'devgaon', 'devgaon tanda', 'dabhrul', 'adgaon', 'antarwali khandi', 'bramhangaon', 'adool tanda', 
                    'parundi', 'tupewadi', 'yasinpur', 'parundi tanda', 'sultanpur', 'georai marda', 'kadethan kh', 'kadethan bk', 'tanda kh', 'tanda bk', 'khadgaon',
                    'ranjangaon dandga', 'sajegaon', 'pachod kh', 'pachod bk', 'limbgaon', 'sonwadi bk', 'inayatpur', 'sonwadi kh', 'kherda', 'nanegaon', 'pusegaon',
                    'harshi kh', 'harshi bk', 'thergaon', 'murma', 'koli bodkha', 'wadji', 'dadegaon kh', 'dadegaon bk', 'dawarwadi', 'dera', 'nandar', 'kaundar',
                    'kutub kheda', 'salwadgaon', 'khandala', 'kekat jalgaon', 'mirkheda', 'chinchala', 'hiwara chondhala', 'vihamandwa', 'bramhagaon', 'hingani',
                    'indegaon', 'apegaon', 'mayagaon', 'navgaon', 'takali ambad', 'hiradpuri', 'pimpalwadi pirachi', 'dalwadi', 'mudhalwadi', 'katpur', 'karanj kheda',
                    'rahatgaon', 'solanapur', 'shringarwadi', 'anandpur', 'akhatwada', 'panthewadi', 'waghadi', 'wadwali', 'dadegaon jahagir', 'pategaon', 'chanakwadi',
                    'telwadi', 'kawasan', 'sonwadi kh', 'mahamadpur', 'ghari', 'ismailpur', 'changatpuri', 'saigaon', 'naigaon', 'lakhephal', 'chitegaon', 'paithan'
                ]
            }
            
        }
        
        # jharkhand_data = {
        #     'Saraikela Kharsawan' : {
        #         'gobindpur rajnagar' : [
        #             'chorbandha', 'gopalpur', 'jota', 'tipangtanr', 'mundakati', 'bharatpur', 'bara kunabera', 'chota kunabera', 'majgaon', 'bisrampur',
        #             'bidri', 'batarbera', 'kendmundi', 'bend kalsai', 'balarampur', 'gangadihi', 'tuibasa', 'sosodih', 'gengeruri', 'khair kocha', 'bana', 'tengrani', 
        #             'kolabaria', 'chhelkani', 'chapra', 'dumardiha', 'burudih', 'bikrampur', 'saragchira', 'haumanada', 'barakanki', 'bhalubasa', 'chhota khiri', 
        #             'sidadih', 'bara khiri', 'baljori', 'baramtalia', 'bankhairbani', 'bera kudar', 'matkumbera', 'padnam sahi', 'sosomuli', 'salbani', 'tangarjora', 
        #             'kesar sara', 'lakhiposi', 'paharpur', 'tumung', 'antusahi', 'nagadi', 'chaliama', 'batujhar', 'barsasai', 'gumdipani', 'bhuyanachna', 'mahesh kudar',
        #             'bongadandu', 'bandi', 'gopinathpur', 'adarhatu', 'ranjor', 'chhota kanki', 'kuorda', 'sanjar', 'lakshmiposi', 'lakshmipur', 'nichintpur', 
        #             'muhuldiha', 'bankati', 'asua', 'baridih', 'bara dholadih', 'ranigunj', 'chota dholadih', 'chheria pahari', 'kendmuri', 'hakasara', 'gura', 'jarkan',
        #             'tentla', 'tentidih', 'kamalpur', 'sobhapur', 'nayasai', 'dandu', 'khairbani', 'pachrikutung', 'rupanachra', 'edal', 'natairuri', 'nayadih', 'dumardiha',
        #             'sonardi', 'hesal', 'bamankutung', 'golokutung', 'chota sijulata', 'khokro', 'bankati', 'gobindpur', 'amlatala', 'pandugiti', 'baghraisai', 'bariasai', 
        #             'kushnopur', 'kurma', 'jogitopa', 'bara paharpur', 'chhota paharpur', 'sarangpos', 'madanasai', 'magarkola', 'namibera', 'changua', 'murumdih',
        #             'rajnagar', 'hensra', 'muriapara', 'gangdesai', 'majgaon', 'gamaria', 'karko', 'solgaria', 'rutudih', 'urughutu', 'bara sijulata', 'patahesal', 'dangardiha', 
        #             'gobardhan', 'rampur', 'phuphundi', 'muchiasai', 'itapokhar', 'jambani', 'jumal', 'teasara', 'chhota kadal', 'bara kadal', 'ichamara', 'rora', 'chadri', 
        #             'nauka', 'gajidih', 'kalajharna', 'maharajganj', 'khandadera', 'kesargaria', 'kotarichara', 'bahadurganj', 'bandu', 'patakocha', 'rabankocha', 'burisiring',
        #             'richituka', 'barubera', 'letoteril', 'chakradharpur', 'dubrajpur', 'chaunradih', 'hanumatbera', 'phuljhari', 'radhanagar', 'jamdih', 'suriaposi', 
        #             'hatnabera', 'sursi', 'khairbani', 'barhai', 'bhursa', 'burudih', 'utidih', 'chota bana', 'dholadih', 'puha', 'katanga', 'kerki', 'gangidih', 'bandna',
        #             'chokay', 'komdih', 'rola', 'somar sai', 'bajadih', 'arjunbila', 'pukhuria', 'raghunathpur', 'kumrasol', 'uparsira', 'arahasa', 'kamarbasa', 'keshargaria', 
        #             'bhurkuli', 'kashida', 'bardih', 'dhuripada', 'jonbani', 'dhanudihi', 'atodih', 'rangamatia', 'joddiha', 'barhai', 'patka', 'telai', 'chailma', 'bankasai',
        #             'lodha', 'soso', 'kuju', 'rengalbera', 'icha', 'dehuridih', 'hensal', 'baddihi', 'bita', 'bisrampur', 'amla tala', 'bhalupani', 'jhalak', 'seresai', 'sitani',
        #             'rajabasa', 'baragidi', 'shyam sunderpur', 'chotagidi', 'seni', 'hatisiring', 'dholadih', 'jadudih', 'kita', 'songria', 'senaposhi', 'gulia', 'herma',
        #             'sarjamdih', 'mahuldiha', 'chandankshiri', 'nimdih', 'kerugot', 'dangardiha', 'majgaon', 'balidih', 'bandadih', 'gondamara'
        #         ]
        #     }
        # }
        
        jharkhand_data = {
            'Saraikela Kharsawan': {
                'gobindpur rajnagar': [
                    # Villages formatted in groups of 10 for better readability
                    ('chorbandha', 379463), ('gopalpur', 379464), ('jota', 379465), ('tipangtanr', 379467), ('mundakati', 379468), 
                    ('bharatpur', 379469), ('bara kunabera', 379470), ('chota kunabera', 379471), ('majgaon', 379713), ('bisrampur', 379688),
                    
                    ('bidri', 379474), ('batarbera', 379475), ('kendmundi', 379476), ('bend kalsai', 379477), ('balarampur', 379478), 
                    ('gangadihi', 379479), ('tuibasa', 379480), ('sosodih', 379481), ('gengeruri', 379482), ('khair kocha', 379483),
                    
                    ('bana', 379484), ('tengrani', 379485), ('kolabaria', 379486), ('chhelkani', 379487), ('chapra', 379488), 
                    ('dumardiha', 379556), ('burudih', 379640), ('bikrampur', 379491), ('saragchira', 379492), ('haumanada', 379493),
                    
                    ('barakanki', 379494), ('bhalubasa', 379495), ('chhota khiri', 379496), ('sidadih', 379497), ('bara khiri', 379498), 
                    ('baljori', 379499), ('baramtalia', 379500), ('bankhairbani', 379501), ('bera kudar', 379502), ('matkumbera', 379503),
                    
                    ('padnam sahi', 379504), ('sosomuli', 379505), ('salbani', 379506), ('tangarjora', 379507), ('kesar sara', 379508), 
                    ('lakhiposi', 379509), ('paharpur', 379510), ('tumung', 379511), ('antusahi', 379512), ('nagadi', 379513),
                    
                    ('chaliama', 379514), ('batujhar', 379515), ('barsasai', 379516), ('gumdipani', 379517), ('bhuyanachna', 379518), 
                    ('mahesh kudar', 379519), ('bongadandu', 379520), ('bandi', 379521), ('gopinathpur', 379522), ('adarhatu', 379523),
                    
                    ('ranjor', 379524), ('chhota kanki', 379525), ('kuorda', 379527), ('sanjar', 379528), ('lakshmiposi', 379529), 
                    ('lakshmipur', 379530), ('nichintpur', 379531), ('muhuldiha', 379532), ('bankati', 379563), ('asua', 379534),
                    
                    ('baridih', 379535), ('bara dholadih', 379536), ('ranigunj', 379537), ('chota dholadih', 379538), ('chheria pahari', 379539), 
                    ('kendmuri', 379540), ('hakasara', 379541), ('gura', 379542), ('jarkan', 379543), ('tentla', 379544),
                    
                    ('tentidih', 379545), ('kamalpur', 379546), ('sobhapur', 379547), ('nayasai', 379548), ('dandu', 379549), 
                    ('khairbani', 379637), ('pachrikutung', 379551), ('rupanachra', 379552), ('edal', 379553), ('natairuri', 379554),
                    
                    ('nayadih', 379555), ('sonardi', 379557), ('hesal', 379558), ('bamankutung', 379559), ('golokutung', 379560), 
                    ('chota sijulata', 379561), ('khokro', 379562), ('bankati', 379563), ('gobindpur', 379564), ('amlatala', 379565),
                    
                    ('pandugiti', 379566), ('baghraisai', 379567), ('bariasai', 379568), ('kushnopur', 379569), ('kurma', 379570), 
                    ('jogitopa', 379571), ('bara paharpur', 379573), ('chhota paharpur', 379574), ('sarangpos', 379575), ('madanasai', 379576),
                    
                    ('magarkola', 379577), ('namibera', 379578), ('changua', 379579), ('murumdih', 379581), ('rajnagar', 379582), 
                    ('hensra', 379583), ('muriapara', 379584), ('gangdesai', 379585), ('gamaria', 379587), ('karko', 379588),
                    
                    ('solgaria', 379589), ('rutudih', 379590), ('urughutu', 379591), ('bara sijulata', 379592), ('patahesal', 379593), 
                    ('dangardiha', 379712), ('gobardhan', 379595), ('rampur', 379596), ('phuphundi', 379597), ('muchiasai', 379598),
                    
                    ('itapokhar', 379599), ('jambani', 379600), ('jumal', 379601), ('teasara', 379602), ('chhota kadal', 379603), 
                    ('bara kadal', 379604), ('ichamara', 379606), ('rora', 379607), ('chadri', 379608), ('nauka', 379609),
                    
                    ('gajidih', 379610), ('kalajharna', 379611), ('maharajganj', 379613), ('khandadera', 379614), ('kesargaria', 379615), 
                    ('kotarichara', 379616), ('bahadurganj', 379617), ('bandu', 379619), ('patakocha', 379620), ('rabankocha', 379621),
                    
                    ('burisiring', 379622), ('richituka', 379623), ('barubera', 379624), ('letoteril', 379625), ('chakradharpur', 379626), 
                    ('dubrajpur', 379627), ('chaunradih', 379628), ('hanumatbera', 379629), ('phuljhari', 379630), ('radhanagar', 379632),
                    
                    ('jamdih', 379633), ('suriaposi', 379634), ('hatnabera', 379635), ('sursi', 379636), ('barhai', 379672), 
                    ('bhursa', 379639), ('utidih', 379641), ('chota bana', 379642), ('dholadih', 379700), ('puha', 379644),
                    
                    ('katanga', 379645), ('kerki', 379646), ('gangidih', 379647), ('bandna', 379648), ('chokay', 379649), 
                    ('komdih', 379651), ('rola', 379652), ('somar sai', 379653), ('bajadih', 379654), ('arjunbila', 379655),
                    
                    ('pukhuria', 379656), ('raghunathpur', 379657), ('kumrasol', 379658), ('uparsira', 379659), ('arahasa', 379660), 
                    ('kamarbasa', 379661), ('keshargaria', 379662), ('bhurkuli', 379663), ('kashida', 379664), ('bardih', 379665),
                    
                    ('dhuripada', 379666), ('jonbani', 379667), ('dhanudihi', 379668), ('atodih', 379669), ('rangamatia', 379670), 
                    ('joddiha', 379671), ('barhai', 379672), ('patka', 379673), ('telai', 379674), ('chailma', 379675),
                    
                    ('bankasai', 379676), ('lodha', 379677), ('soso', 379678), ('kuju', 379679), ('rengalbera', 379680), 
                    ('icha', 379681), ('dehuridih', 379684), ('hensal', 379685), ('baddihi', 379686), ('bita', 379687),
                    
                    ('bisrampur', 379688), ('amla tala', 379689), ('bhalupani', 379690), ('jhalak', 379691), ('seresai', 379692), 
                    ('sitani', 379693), ('rajabasa', 379694), ('baragidi', 379695), ('shyam sunderpur', 379696), ('chotagidi', 379697),
                    
                    ('seni', 379698), ('hatisiring', 379699), ('dholadih', 379700), ('jadudih', 379701), ('kita', 379702), 
                    ('songria', 379703), ('senaposhi', 379704), ('gulia', 379705), ('herma', 379706), ('sarjamdih', 379707),
                    
                    ('mahuldiha', 379708), ('chandankshiri', 379709), ('nimdih', 379710), ('kerugot', 379711), ('dangardiha', 379712), 
                    ('majgaon', 379713), ('balidih', 379714), ('bandadih', 379715), ('gondamara', 379716)
                ]
            }
        }

        # Populate Rajasthan data
        rajasthan, created = State.objects.get_or_create(name='Rajasthan')
        self.add_districts(rajasthan, rajasthan_data)

        # Populate Andhra Pradesh data
        andhra_pradesh, created = State.objects.get_or_create(name='Andhra Pradesh')
        self.add_districts(andhra_pradesh, andhra_pradesh_data)

        # Populate Karnataka data
        karnataka, created = State.objects.get_or_create(name='Karnataka')
        self.add_districts(karnataka, karnataka_data)
        
        uttar_pradesh, created = State.objects.get_or_create(name='Uttar Pradesh')
        self.add_districts(uttar_pradesh, uttar_pradesh_data)
        
        maharashtra, created = State.objects.get_or_create(name='Maharashtra')
        self.add_districts(maharashtra, maharashtra_data)
        
        jharkhand, created = State.objects.get_or_create(name='Jharkhand')
        self.add_districts(jharkhand, jharkhand_data)
        

        self.stdout.write(self.style.SUCCESS('Successfully populated the RDS instance with location data.'))