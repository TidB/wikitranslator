# STANDARD
ADDEDTOGAME = "该物品被添加到游戏中。"
ALLCLASSESBOX = "[[All classes/zh-hans|全兵种]]"
ITEMLOOK = "" # not matches Chinese translation very well
NOUNMARKER_INDEFINITE_COSMETIC = "一件"
NOUNMARKER_INDEFINITE_SET = "一个"
NOUNMARKER_INDEFINITE_WEAPON = "一把"

SENTENCE_1_ALL = "'''{{{{item name|{item_name}}}}}（{item_name}）'''是{noun_marker}{promotional}{workshop_link}{class_list}{item_type}。"
SENTENCE_1_COMMUNITY_COSMETIC = "由[[Steam Workshop/zh-hans|社区]]玩家制作的"
SENTENCE_1_COMMUNITY_WEAPON = "由[[Steam Workshop/zh-hans|社区]]玩家制作的"
SENTENCE_1_PROMO_COSMETIC = "在[[Promotional items/zh-hans|促销活动]]中加入的"
SENTENCE_1_PROMO_WEAPON = "在[[Promotional items/zh-hans|促销活动]]中加入的"
SENTENCE_1_COSMETIC = "[[Cosmetic Item/zh-hans|饰品]]"
SENTENCE_1_SET = "[[Item set/zh-hans|物品套装]]"
SENTENCE_1_CLASSES_ALL = "[[Classes/zh-hans|全兵种]]通用"
SENTENCE_1_CLASSES_ONE = "[[{class_name}/zh-hans|{loc_class_name}]]专属"
SENTENCE_1_CLASSES_MORE = "与[[{class_name}/zh-hans|{loc_class_name}]]通用" # manually remove redundant "专属" or "通用".
SENTENCE_1_CLASSES_AND = "与"
SENTENCE_1_CLASSES_COMMA = "，"

SENTENCE_COMMUNITY = "{{{{item name|{item_name}}}}}是被{workshop_link}到[[Steam Workshop/zh-hans|Steam创意工坊]]的。"
SENTENCE_COMMUNITY_LINK = "[{link} 贡献]"
SENTENCE_COMMUNITY_NAME = ""

SENTENCE_PROMOTIONAL = "{date}{steam}购买了《[[{game_name}/zh-hans|{loc_class_name}]]》的玩家，会收到[[Genuine/zh-hans|纯正]]品质的{{{{item name|{item_name}}}}}作为奖励。"
SENTENCE_PROMOTIONAL_STEAM = "于[[Steam/zh-hans|Steam]]上"
SENTENCE_PROMOTIONAL_DATE = "在{date}之前"

SENTENCE_SET = "" # not used anymore
SENTENCE_SET_INCLUDES = "该套装包含以下物品："

SENTENCE_THUMBNAIL = "{{{{item name|{item_name}}}}}的创意工坊缩略图"

SENTENCE_1_SUB_PRIMARY = "[[Weapon/zh-hans#{class_name}primary|主武器]]"
SENTENCE_1_SUB_SECONDARY = "[[Weapon/zh-hans#{class_name}secondary|副武器]]"
SENTENCE_1_SUB_MELEE = "[[Weapon/zh-hans#{class_name}melee|近战武器]]"

ITEM_FLAGS = {
    "not usable in crafting": "不可参与合成",
    "not tradable": "不可交易",
    "not tradable or usable in crafting": "不可交易或参与合成",
}

ATTRIBUTES = {
    "achievement item: not tradable": "成就物品：不可交易",
    "holiday restriction: tf birthday": "节日使用限制：军团要塞生日",
    "holiday restriction: winter": "", # not found in localization files
    "holiday restriction: halloween": "节日限制：万圣节",
    "holiday restriction: halloween / full moon": "节日限制：万圣节/满月之夜",
    "holiday restriction: halloween / full moon / valentine's day": "节日限制：万圣节/满月之夜/情人节",
}

CLASSES = {
    "Scout": "侦察兵",
    "Soldier": "士兵",
    "Pyro": "火焰兵",
    "Demoman": "爆破手",
    "Heavy": "机枪手",
    "Engineer": "工程师",
    "Medic": "医生",
    "Sniper": "狙击手",
    "Spy": "间谍",
}

HEADINGS = {
    'as a crafting ingredient': "作为合成材料",
    'blueprint': "蓝图",
    'bugs': "漏洞",
    'crafting': "合成",
    'damage and function times': "伤害和作用时间",
    'external links': "外部链接",
    'gallery': "画廊",
    'item set': "物品套装",
    'notes': "注释",
    'painted variants': "染色预览",
    'references': "参考内容",
    'related achievements': "相关成就",
    'see also': "参见",
    'strange variant': "奇异属性",
    'styles': "式样",
    'trivia': "细枝末节",
    'unused content': "未使用内容",
    'update history': "更新历史",
}

ITEM_LEVELS = {
    'Apparel': "服装",
    'Armband': "武装带",
    'Aura of Incorruptibility': "正直光环",
    'Backpack': "背包",
    'Badge': "徽章",
    'Balloon': "气球",
    'Bandages': "绷带",
    'Bandana': "花色丝质大手帕",
    'Bandolier': "子弹带",
    'Barbeque': "烧烤用品",
    'Beach Towel': "海滩浴巾",
    'Bells': "铃铛",
    'Bird Head': "鸟头",
    'Blueprints': "蓝图",
    'Bones': "骨骼",
    'Bongos': "小鼓",
    'Boots': "靴子",
    'Botkiller': "机器人毁灭者",
    'Cape': "斗篷",
    'Championship Belt': "冠军腰带",
    'Cigar': "雪茄",
    'Coat': "外套",
    'Coffin': "棺材",
    'Community Medal': "社区勋章",
    'Conscience': "良心",
    'Cooler': "冷藏箱",
    'Cosmetic Armor': "装饰用盔甲",
    'Cosmetic Augmentation': "装饰性身体改造",
    'Cosmetic Axe': "装饰用斧头",
    'Cosmetic Knife': "装饰用刀子",
    'Costume Piece': "服装",
    'Decorative Bombs': "装饰用炸弹",
    'Duck': "鸭子",
    'Electronic Device': "电子仪器",
    'Eye Stalks': "眼柄",
    'Facial Hair': "胡子",
    'Flair!': "漂亮的小徽章",
    'Flip-Flops': "人字拖",
    'Fuel Tank': "燃料罐",
    'Func_Medal': "", # not found in localization files
    'Futuristic Sound Device': "未来主义风格音响设备",
    'Ghost': "鬼魂",
    'Glasses': "眼镜",
    'Glove': "手套",
    'Gloves': "手套",
    'Golf Clubs': "",
    'Hair': "头发",
    'Hat': "帽子",
    'Headgear': "头饰",
    'Headset': "头戴式显示器",
    'Helmet': "头盔",
    'Holiday Hat': "节日帽",
    'Hooves': "蹄子",
    'Kilt': "苏格兰褶裥短裙",
    'Lantern': "灯笼",
    'Lunchbox': "饭盒",
    'Mascot': "吉祥物",
    'Mask': "面具",
    'Medal': "勋章",
    'Medallion': "奖章",
    'Mystical Lamp': "神灯",
    'Necklace': "项链",
    'Photograph': "照片",
    'Pin': "胸针",
    'Pipe': "烟斗",
    'Pocket Buddy': "口袋伙计",
    'Pocket Square': "口袋方块",
    'Poncho': "斗篷",
    'Puffy Shirt': "宽松衬衫",
    'Pyrovision Goggles': "护目镜",
    'Refreshment': "点心",
    'Ring': "钻戒",
    'Robot': "机器人",
    'Safety Apparatus': "安全装置",
    'Satchel': "小包",
    'Scarf': "围巾",
    'Science Project': "科学项目",
    'Shield': "衬衫",
    'Shirt': "衬衫",
    'Shoes': "鞋子",
    'Skateboard': "滑板",
    'Sled': "雪橇",
    'Snow Globe': "雪景球",
    'Spikes': "跑鞋",
    'Spirit Animal': "小动物",
    'Spooky Companion': "幽灵同伴",
    'Spurs': "靴刺",
    'Squirrel': "松鼠",
    'Stethoscope': "听诊器",
    'Stocking': "袜子",
    'Supplies': "补给品",
    'Tattoos': "刺青",
    'Tentacles': "触手",
    'Tournament Medal': "锦标赛奖牌",
    'Towel': "毛巾",
    'Treasure': "宝箱",
    'Tuxedo': "燕尾服",
    'Undead Pet': "亡灵宠物",
    'Uniform': "制服",
    "Veteran's Beret": "",
    'Wings': "翅膀",
}