import argparse
import json
import sys
from pathlib import Path
from typing import Any


RETRIEVED_AT = "2026-04-14"
SOURCE_URLS = [
    "https://zh.wikipedia.org/zh-cn/%E7%81%AB%E5%BD%B1%E5%BF%8D%E8%80%85",
    "https://zh.wikipedia.org/zh-sg/%E7%81%AB%E5%BD%B1%E5%BF%8D%E8%80%85%E8%A7%92%E8%89%B2%E5%88%97%E8%A1%A8",
]
SOURCE_POLICY = "归纳摘要并结构化为同人写作一致性锚点，不保存网页长段原文。"


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parts(value: str) -> list[str]:
    return [item for item in value.split("|") if item]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_source(data: dict[str, Any]) -> None:
    data["schema_version"] = "1.1"
    source = data.setdefault("source", {})
    if not isinstance(source, dict):
        data["source"] = source = {}
    urls = source.setdefault("additional_reference_urls", [])
    for url in SOURCE_URLS:
        if url not in urls and source.get("reference_url") != url and source.get("url") != url:
            urls.append(url)
    source["last_enriched_at"] = RETRIEVED_AT
    source.setdefault("policy", SOURCE_POLICY)


def merge_records(data: dict[str, Any], collection_name: str, records: list[dict[str, Any]]) -> int:
    collection = data.setdefault(collection_name, [])
    if not isinstance(collection, list):
        raise TypeError(f"{collection_name} must be a list")
    existing_ids = {record.get("id") for record in collection if isinstance(record, dict)}
    added = 0
    for record in records:
        record_id = record.get("id")
        if record_id in existing_ids:
            continue
        collection.append(record)
        existing_ids.add(record_id)
        added += 1
    return added


def character(record: tuple[str, ...]) -> dict[str, Any]:
    (
        record_id,
        name_zh,
        aliases,
        category,
        home_village,
        affiliations,
        life_status,
        roles,
        abilities,
        secrets,
        risks,
        anchors,
    ) = record
    return {
        "id": record_id,
        "name_zh": name_zh,
        "aliases": parts(aliases),
        "category": category,
        "home_village": home_village,
        "affiliations": parts(affiliations),
        "life_status_canon_end": life_status,
        "roles": parts(roles),
        "signature_abilities": parts(abilities),
        "sensitive_secrets": parts(secrets),
        "continuity_risks": parts(risks),
        "canon_anchor_ids": parts(anchors),
    }


CHARACTER_ROWS = [
    ("chiyo", "千代", "千代婆婆", "canon_support", "sunagakure", "sunagakure|puppet_corps", "dead", "elder|puppet_master|medical_knowledge_holder", "puppet_technique|life_transfer_jutsu|poison_and_antidote", "一尾抽离救援代价|砂隐傀儡与毒术经验", "千代复活我爱罗需要生命交换，不能无代价治疗。|她的牺牲影响砂隐对鸣人与木叶的观感。", "canon_008_kazekage_rescue"),
    ("mifune", "三船", "铁之国大将|武士三船", "canon_support", "land_of_iron", "land_of_iron_samurai|shinobi_allied_forces", "alive", "samurai_general|summit_moderator", "iaido|samurai_chakra_blade", "五影会谈中立地位|半藏旧战因缘", "铁之国是武士政治空间，不应完全按忍村任务体系处理。|五影会谈地点和中立性变化会牵动国际政治。", "canon_013_five_kage_summit|canon_015_war_escalation"),
    ("gamabunta", "蛤蟆文太", "文太|蛤蟆老大", "summon", "mount_myoboku", "mount_myoboku|jiraiya_contract_line|uzumaki_naruto_contract_line", "alive", "boss_summon|battlefield_support", "toad_blade|oil_combo|large_scale_summon_combat", "妙木山契约关系|鸣人通灵成长节点", "大型通灵需要查克拉和契约资格，不能随叫随到当坐骑。|文太性格强势，召唤者必须压得住场。", "canon_002_chunin_exam|canon_003_konoha_crush"),
    ("fukasaku", "深作", "深作仙人|蛤蟆仙人", "summon", "mount_myoboku", "mount_myoboku", "alive", "sage_teacher|battle_support", "sage_mode_training|frog_kata_support|toad_genjutsu_combo", "仙术修炼方法|佩恩情报传递", "仙术训练需要地点、时间、静止条件和自然能量风险。", "canon_012_pain_assault"),
    ("shima", "志麻", "志麻仙人|蛤蟆婆婆", "summon", "mount_myoboku", "mount_myoboku", "alive", "sage_support|toad_genjutsu_user", "toad_genjutsu_combo|summon_support", "妙木山仙术体系", "蛤蟆临唱等组合技需要配合与准备，不是瞬发控制。", "canon_011_jiraiya_pain_sasuke_itachi|canon_012_pain_assault"),
    ("katsuyu", "蛞蝓", "活蝓|蛞蝓大人", "summon", "shikkotsu_forest", "shikkotsu_forest|tsunade_contract_line|haruno_sakura_contract_line", "alive", "medical_summon|wide_area_healing_support", "split_body|chakra_transmission|acid", "百豪/医疗查克拉联动", "大范围治疗依赖召唤者查克拉储备，不能无限奶全场。", "canon_012_pain_assault|canon_016_war_finale_kaguya_sasuke"),
    ("manda", "万蛇", "大蛇通灵兽", "summon", "ryuchi_cave_or_snake_contract", "orochimaru_contract_line", "dead", "boss_summon|dangerous_contract_beast", "giant_snake_combat|high_mobility", "大蛇丸通灵契约代价", "万蛇性格凶暴且索要祭品，不能写成忠犬式通灵兽。", "canon_004_search_tsunade|canon_011_jiraiya_pain_sasuke_itachi"),
    ("pakkun", "帕克", "忍犬帕克", "summon", "konohagakure_contract", "hatake_kakashi_contract_line", "alive", "tracking_summon|intel_support", "scent_tracking|message_delivery", "卡卡西追踪任务细节", "忍犬追踪可破解搜索难题，使用前要考虑气味、地形和时间。", "canon_005_sasuke_retrieval"),
    ("yuhi_kurenai", "夕日红", "红老师|夕日老师", "canon_support", "konohagakure", "team_8|konohagakure", "alive", "jonin_sensei|genjutsu_specialist", "genjutsu_tree_binding", "阿斯玛关系|第八班成长节奏", "幻术专精不等于能压制万花筒级瞳术。|怀孕/家庭线会影响疾风传后续出场。", "canon_002_chunin_exam|canon_010_hidan_kakuzu"),
    ("hyuga_hiashi", "日向日足", "日足|日向族长", "canon_support", "konohagakure", "hyuga_clan|konohagakure", "alive", "clan_head|byakugan_user", "byakugan|gentle_fist", "日向宗分家制度|云隐绑架事件余波", "日向政治不是单个父亲态度问题，宗家/分家制度要作为压力源。", "canon_002_chunin_exam"),
    ("hyuga_hanabi", "日向花火", "花火", "canon_support", "konohagakure", "hyuga_clan|konohagakure", "alive", "hyuga_heir_candidate|byakugan_user", "byakugan|gentle_fist", "日向继承压力", "花火年龄和实力阶段必须匹配时间线。", "canon_002_chunin_exam"),
    ("sarutobi_konohamaru", "猿飞木叶丸", "木叶丸", "canon_support", "konohagakure", "konohagakure|konohamaru_corps", "alive", "academy_student_then_shinobi|naruto_admirer", "rasengan|shadow_clone_jutsu", "三代火影孙子身份", "木叶丸掌握螺旋丸有后续训练因果，不能在过早时间线提前成熟。", "canon_012_pain_assault"),
    ("ebisu", "惠比寿", "特别上忍惠比寿", "canon_support", "konohagakure", "konohagakure|konohamaru_corps", "alive", "tutor|special_jonin", "basic_training|chakra_control_instruction", "木叶丸教学安排", "惠比寿适合教学/保护线，不宜突然写成影级战斗力。", "canon_000_kyuubi_attack_backstory|canon_012_pain_assault"),
    ("mizuki", "水木", "水木老师", "canon_minor", "konohagakure", "konohagakure", "incarcerated_or_defeated", "academy_teacher|early_antagonist", "shurikenjutsu|manipulation", "封印之书事件", "水木是鸣人被伊鲁卡认可的触发器之一，替换他需保留护额/封印之书因果。", "canon_001_land_of_waves"),
    ("baki", "马基", "砂隐马基", "canon_support", "sunagakure", "sunagakure|team_baki", "alive", "jonin_sensei|sand_intel_handler", "wind_blade", "毁灭木叶行动前置合作", "马基涉及砂隐与音隐合谋线，不能只作为普通带队老师。", "canon_002_chunin_exam|canon_003_konoha_crush"),
    ("darui", "达鲁伊", "达鲁伊", "canon_support", "kumogakure", "kumogakure|shinobi_allied_forces", "alive", "raikage_guard|war_division_commander", "black_lightning|storm_release", "云隐高层部署", "岚遁/黑雷属于高阶能力，出场要匹配云隐精英身份。", "canon_013_five_kage_summit|canon_015_war_escalation"),
    ("samui", "萨姆伊", "萨姆依", "canon_support", "kumogakure", "team_samui|kumogakure", "alive", "cloud_jonin|intel_messenger", "kenjutsu|team_command", "佐助袭击奇拉比后的云隐外交压力", "云隐小队来木叶会触发外交程序，不应像普通路人队一样处理。", "canon_013_five_kage_summit"),
    ("karui", "卡鲁伊", "卡鲁依", "canon_support", "kumogakure", "team_samui|kumogakure", "alive", "cloud_chunin_or_jonin|killer_bee_rescue_related", "kenjutsu", "奇拉比失踪后的情绪压力", "卡鲁伊对鸣人的冲突源于云隐情报和奇拉比事件，不能随便改成无因挑衅。", "canon_013_five_kage_summit"),
    ("omoi", "奥摩伊", "奥莫伊", "canon_support", "kumogakure", "team_samui|kumogakure", "alive", "cloud_shinobi|overthinking_teammate", "kenjutsu|lightning_release", "奇拉比失踪后的云隐任务", "奥摩伊适合紧张吐槽和战术焦虑，但不能变成纯搞笑角色。", "canon_013_five_kage_summit"),
    ("ao", "青", "雾隐青", "canon_support", "kirigakure", "kirigakure|mizukage_guard", "alive_or_later_boruto_state", "sensor|byakugan_transplant_user", "sensor_ninjutsu|byakugan_transplant", "移植白眼来源|五影会谈感知情报", "青的白眼是移植而非日向血统，使用和政治含义都要记录。", "canon_013_five_kage_summit"),
    ("chojuro", "长十郎", "长十郎", "canon_support", "kirigakure", "kirigakure|seven_ninja_swordsmen", "alive", "mizukage_guard|swordsman", "hiramekarei", "雾隐忍刀继承", "长十郎早期性格怯弱但战斗能力强，不能只写成软弱背景板。", "canon_013_five_kage_summit"),
    ("kurotsuchi", "黑土", "黑土", "canon_support", "iwagakure", "iwagakure", "alive", "tsuchikage_guard|future_tsuchikage", "lava_release|earth_release", "岩隐高层继承线", "黑土关联岩隐继任政治，不能只作为护卫消耗。", "canon_013_five_kage_summit|canon_015_war_escalation"),
    ("akatsuchi", "赤土", "赤土", "canon_support", "iwagakure", "iwagakure", "alive", "tsuchikage_guard|earth_release_specialist", "earth_release_golem", "岩隐护卫部署", "赤土适合承担护卫与重装防线，不应无故离开土影保护职责。", "canon_013_five_kage_summit"),
    ("tayuya", "多由也", "多由也", "canon_minor_antagonist", "otogakure", "sound_four|orochimaru_camp", "dead", "sound_four_member|genjutsu_user", "demon_flute_genjutsu|curse_mark", "音忍四人众护送佐助任务", "音忍四人众死亡/存活会直接改变佐助夺还战人员与伤亡。", "canon_005_sasuke_retrieval"),
    ("kidomaru", "鬼童丸", "鬼童丸", "canon_minor_antagonist", "otogakure", "sound_four|orochimaru_camp", "dead", "sound_four_member|ranged_tactician", "spider_web_jutsu|curse_mark", "音忍四人众护送佐助任务", "鬼童丸对宁次成长节点关键，改写后要替代宁次的生死突破。", "canon_005_sasuke_retrieval"),
    ("jirobo", "次郎坊", "次郎坊", "canon_minor_antagonist", "otogakure", "sound_four|orochimaru_camp", "dead", "sound_four_member|strength_type", "earth_dome_prison|curse_mark", "音忍四人众护送佐助任务", "次郎坊对丁次成长和秋道秘药代价关键，不能随意移除。", "canon_005_sasuke_retrieval"),
    ("sakon_ukon", "左近右近", "左近|右近", "canon_minor_antagonist", "otogakure", "sound_four|orochimaru_camp", "dead", "sound_four_member|body_merge_user", "body_merge|curse_mark", "音忍四人众护送佐助任务", "左近右近与牙/赤丸战损、勘九郎救援强相关。", "canon_005_sasuke_retrieval"),
]


def jutsu(record: tuple[str, ...]) -> dict[str, Any]:
    record_id, name_zh, aliases, type_name, rank, nature, users, prereq, cost, limitations, counters, risk = record
    return {
        "id": record_id,
        "name_zh": name_zh,
        "aliases": parts(aliases),
        "type": type_name,
        "rank": rank,
        "nature": parts(nature),
        "known_users": parts(users),
        "prerequisites": parts(prereq),
        "cost": cost,
        "limitations": parts(limitations),
        "counters": parts(counters),
        "continuity_risk": risk,
    }


JUTSU_ROWS = [
    ("summoning_jutsu", "通灵之术", "通灵术|召唤术", "space_time_contract_ninjutsu", "C_to_A_by_scale", "", "jiraiya|orochimaru|tsunade|uzumaki_naruto|hatake_kakashi", "blood_contract|chakra_payment|hand_signs", "scales_with_summon_size", "需要契约或特殊媒介|大型通灵消耗巨大|通灵兽有自主意志", "打断结印|封锁空间|压制召唤者查克拉", "通灵兽不是免费道具；契约来源、大小、性格和消耗必须记录。"),
    ("medical_ninjutsu", "医疗忍术", "掌仙术|医疗术", "ninjutsu_support", "variable", "", "tsunade|haruno_sakura|shizune|yakushi_kabuto", "fine_chakra_control|anatomy_knowledge|training_time", "depends_on_injury_severity", "不能无视死亡边界|毒素/经络/器官伤需要诊断|战场治疗会暴露医疗忍者", "持续追击|毒素复杂化|查克拉干扰", "医疗忍术不能当万能复活术；重大伤势必须留下恢复期或代价。"),
    ("chakra_enhanced_strength", "怪力", "查克拉怪力|纲手怪力", "chakra_control_taijutsu", "A", "", "tsunade|haruno_sakura", "extreme_chakra_control|physical_training", "burst_chakra", "命中窗口要求高|地形破坏会影响友军|控制不足会自伤", "远程牵制|高速闪避|柔性卸力", "怪力来自高精度控制和训练，不是单纯力气大。"),
    ("creation_rebirth", "创造再生", "创造再生之术", "medical_forbidden_jutsu", "S", "", "tsunade", "byakugo_seal|massive_chakra_storage|medical_mastery", "shortens_lifespan_or_cell_division_limit", "不能无限重置身体|依赖预存查克拉|战后负担极高", "封印|持续高强度压制|查克拉吸收", "创造再生有寿命/细胞分裂代价，不能变成无冷却回血。"),
    ("byakugo_seal", "百豪之印", "百豪|阴封印", "chakra_storage_seal", "S", "", "tsunade|haruno_sakura", "long_term_chakra_storage|precise_control", "years_of_storage_and_release_burden", "形成需要长期积累|释放后需重新储备|不等于无限查克拉", "封印干扰|查克拉吸收|逼迫提前消耗", "百豪必须记录储备进度和释放后状态。"),
    ("amaterasu", "天照", "黑炎", "mangekyo_dojutsu", "S", "fire_like_dojutsu", "uchiha_itachi|uchiha_sasuke", "mangekyo_sharingan|eye_specific_ability", "high_eye_strain_and_chakra", "视线命中依赖|可被剥离/封印/高速规避|大量使用导致视力恶化", "提前遮挡|高速移动|封印术|脱壳或断肢规避", "天照不能无脑秒杀所有敌人；视力消耗和命中条件必须出现。"),
    ("tsukuyomi", "月读", "月读幻术", "mangekyo_genjutsu", "S", "yin", "uchiha_itachi", "mangekyo_sharingan|eye_contact", "severe_eye_strain", "需要目光接触|对瞳力/精神力强者风险升高|频繁使用会加速恶化", "避免对视|瞳术对抗|外部打断", "月读是高压幻术，不应用作普通审讯工具刷屏。"),
    ("kotoamatsukami", "别天神", "最强幻术|止水眼", "mangekyo_genjutsu", "S", "yin", "uchiha_shisui|shimura_danzo|uchiha_itachi", "shisui_mangekyo_eye", "very_long_cooldown_or_hashirama_cell_modifier", "冷却极长|眼位和持有者必须明确|政治后果巨大", "提前发现瞳术|夺眼|封印或隔绝视线", "别天神会破坏角色意志与政治线，任何使用都必须成为重大事件。"),
    ("izanagi", "伊邪那岐", "改写现实", "forbidden_dojutsu", "S", "yin_yang", "uchiha_madara|shimura_danzo", "sharingan|uchiha_or_implant_conditions", "eye_blindness", "持续时间有限|每只眼消耗一次|移植眼需适配", "拖延持续时间|情报识破|封锁身体行动", "伊邪那岐必须消耗眼睛，不能作为无代价重开。"),
    ("izanami", "伊邪那美", "命运循环", "forbidden_dojutsu", "S", "yin", "uchiha_itachi", "sharingan|setup_loop_events", "eye_blindness", "需要构建感官循环|目标需陷入自我逃避主题|使用者牺牲眼睛", "接受现实解除|打断前置构建", "伊邪那美是主题性封印幻术，不是普通控场技能。"),
    ("gentle_fist", "柔拳", "日向柔拳", "byakugan_taijutsu", "B_to_A", "", "hyuga_neji|hyuga_hinata|hyuga_hiashi|hyuga_hanabi", "byakugan|tenketsu_knowledge|taijutsu_training", "precision_chakra", "需要近身|对高防御/非人结构需调整|白眼视野也有盲点", "远程压制|视野盲点利用|高速扰乱", "柔拳强在点穴和查克拉干扰，不是普通拳脚加成。"),
    ("eight_trigrams_sixty_four_palms", "八卦六十四掌", "六十四掌", "hyuga_secret_taijutsu", "A", "", "hyuga_neji|hyuga_hiashi|hyuga_hinata", "byakugan|gentle_fist_mastery", "high_precision_and_stamina", "需要把目标拉入八卦领域|被打断会失去连段收益", "脱离近身范围|分身扰乱|范围攻击", "宗家/分家学习边界会影响宁次线，必须看时间点。"),
    ("shadow_imitation", "影子模仿术", "影缚术|影子束缚术", "nara_clan_secret", "B", "yin", "nara_shikamaru|nara_shikaku", "nara_clan_training|shadow_line_of_effect", "chakra_maintenance", "影子长度和光源限制|力量差距会影响控制|维持期间本体受限", "改变光源|切断影子连接|力量挣脱", "影子术适合智斗，不能无视光照与距离。"),
    ("mind_body_switch", "心转身之术", "心转身|山中秘术", "yamanaka_clan_secret", "C_to_B", "yin", "yamanaka_ino|yamanaka_inoichi", "yamanaka_training|mental_targeting", "user_body_incapacitated", "命中失败会暴露本体|控制期间本体无防备|强意志目标可抵抗", "闪避直线锁定|精神防御|攻击施术者本体", "山中秘术必须处理施术者身体安全和情报回传。"),
    ("partial_expansion", "部分倍化术", "倍化术|秋道秘术", "akimichi_clan_secret", "C_to_B", "yang", "akimichi_choji|akimichi_choza", "akimichi_training|calorie_conversion", "calorie_and_chakra_consumption", "体型变化影响机动|过度使用需兵粮丸或恢复|目标大时更易被命中", "灵活拉扯|消耗战|关节限制", "秋道秘术与体能/热量强绑定，秘药有严重代价。"),
    ("fang_over_fang", "牙通牙", "牙通牙", "inuzuka_clan_taijutsu", "C_to_B", "", "inuzuka_kiba", "ninken_partner|beast_mimicry_training", "stamina_and_coordination", "直线突进可被预判|依赖忍犬搭档状态", "气味干扰|地形陷阱|侧向闪避", "牙与赤丸是组合战，忍犬受伤会削弱整套战法。"),
    ("destruction_bug_technique", "寄坏虫", "油女虫术|寄坏虫之术", "aburame_clan_secret", "B", "", "aburame_shino", "aburame_host_body|insect_colony", "long_term_host_symbiosis", "虫群数量和距离限制|火遁/范围攻击可压制|宿主需要保持供养", "大范围火焰|毒雾|查克拉隔绝", "油女秘术是寄生共生体系，不能临时学会。"),
    ("fireball_jutsu", "火遁·豪火球之术", "豪火球|豪火球之术", "fire_release", "C", "fire", "uchiha_sasuke|uchiha_itachi|uchiha_madara", "fire_nature|basic_hand_seals", "medium_for_young_ninja", "直线范围明显|水遁和地形可削弱|幼年使用体现天赋但仍需训练", "water_release|dodging|terrain_cover", "宇智波儿童会豪火球是族内成人认可节点，时间线要谨慎。"),
    ("raikiri", "雷切", "千鸟雷切|卡卡西雷切", "lightning_release_assassination", "S_or_A_variant", "lightning", "hatake_kakashi", "chidori_base|high_speed_charge|visual_tracking_support", "medium_high", "高速突进暴露路线|查克拉消耗限制次数|不适合持续群战", "预判反击|替身诱导|防御忍术", "雷切是卡卡西招牌，次数、查克拉和写轮眼负担要记录。"),
    ("puppet_technique", "傀儡术", "傀儡操演|砂隐傀儡术", "chakra_thread_ninjutsu", "B_to_S", "", "sasori|chiyo|kankuro", "chakra_threads|puppet_build|trap_and_poison_knowledge", "fine_control_and_inventory", "傀儡损坏需维修|毒药/机关需库存|操作者位置和手指动作可被针对", "切线|破坏傀儡|近身压制操作者", "傀儡战必须记录傀儡数量、机关、毒药和维修状态。"),
    ("sand_manipulation", "砂缚/砂操控", "控砂|砂瀑", "sand_ninjutsu_or_jinchuriki_style", "B_to_S", "earth|wind", "gaara", "sand_medium|chakra_control|shukaku_history_or_training", "scales_with_sand_volume", "环境砂量影响效率|水分/重量/速度会改变战斗|大规模防御消耗高", "高速突破|水分干扰|空中机动", "我爱罗控砂阶段受一尾和心理状态影响，抽离后能力边界要重估。"),
    ("sealing_jutsu_general", "封印术", "封印术式|符咒封印", "fuinjutsu", "C_to_S", "", "uzumaki_kushina|namikaze_minato|jiraiya|orochimaru", "seal_formula_knowledge|medium_or_body_anchor|chakra_precision", "depends_on_target_and_formula", "需要术式设计和媒介|错误封印会反噬|高阶封印常有牺牲代价", "解印知识|破坏媒介|外部干扰", "封印术最容易变万能钥匙；必须写清术式来源、媒介、限制和代价。"),
    ("poison_craft", "毒术", "傀儡毒|砂隐毒", "support_assassination", "B_to_A", "", "sasori|chiyo|shizune", "toxin_formula|delivery_method|medical_counter_knowledge", "materials_and_preparation", "需提前制备|解药/医疗忍者可对抗|环境和剂量影响效果", "解毒剂|避开伤口|傀儡机关识破", "毒一旦命中会强改战斗节奏，必须记录剂量、发作时间和解药来源。"),
]


def organization(record: tuple[str, ...]) -> dict[str, Any]:
    record_id, name_zh, aliases, type_name, nation, members, assets, fields, risk = record
    return {
        "id": record_id,
        "name_zh": name_zh,
        "aliases": parts(aliases),
        "type": type_name,
        "nation": nation,
        "leader_history": [],
        "high_impact_members": parts(members),
        "core_assets": parts(assets),
        "canon_conflicts": [],
        "continuity_fields": parts(fields),
        "fanfic_risk": risk,
    }


ORGANIZATION_ROWS = [
    ("team_8", "第八班", "夕日红班|红班", "shinobi_team", "land_of_fire", "hyuga_hinata|inuzuka_kiba|aburame_shino|yuhi_kurenai", "tracking|reconnaissance|byakugan|ninken|insect_scouting", "tracking_assignments|kurenai_status|hinata_confidence|kiba_akamaru_status|shino_insect_colony", "第八班是侦察班，不应长期当正面火力队使用；白眼、嗅觉、虫群会提前发现许多埋伏。"),
    ("team_baki", "马基班", "砂隐三姐弟小队|砂隐小队", "shinobi_team", "land_of_wind", "gaara|temari|kankuro|baki", "sand_jinchuriki|wind_release|puppet_technique", "sand_konoha_alliance|gaara_psychological_state|shukaku_control|sibling_trust", "砂隐小队行动受风之国资源和毁灭木叶计划影响，不能只写成考试路人。"),
    ("team_samui", "萨姆伊小队", "云隐萨姆伊班", "shinobi_team", "land_of_lightning", "samui|karui|omoi", "cloud_diplomatic_pressure|kenjutsu|killer_bee_rescue_context", "bee_status|sasuke_intel|konoha_diplomatic_response|team_morale", "云隐来木叶的冲突是外交压力，不是私人找茬。"),
    ("legendary_sannin", "传说中的三忍", "三忍|木叶三忍", "elite_title_group", "land_of_fire", "jiraiya|tsunade|orochimaru", "toad_contract|slug_contract|snake_contract|medical_mastery|forbidden_research", "member_status|student_lineages|summon_contracts|political_influence", "三忍既是战力标尺也是师承网络，改写任何一人都会牵动鸣人、佐助、小樱成长线。"),
    ("seven_ninja_swordsmen", "忍刀七人众", "雾隐忍刀七人众|七忍刀", "elite_weapon_group", "land_of_water", "zabuza|hoshigaki_kisame|chojuro|suigetsu", "legendary_swords|kirigakure_bloody_mist_legacy", "sword_registry|owner_history|missing_swords|blood_mist_reputation", "忍刀持有权和雾隐政治强绑定，换刀必须记录来源和继承/夺取过程。"),
    ("medical_corps", "医疗班", "医疗部队|木叶医疗班", "support_corps", "varies", "tsunade|haruno_sakura|shizune", "triage|antidote|field_hospital|chakra_healing", "available_medics|hospital_damage|antidote_stock|casualty_overload", "医疗班可降低死亡率，但不能抹平战场代价；医疗资源会成为政治和后勤压力。"),
    ("anbu", "暗部", "暗杀战术特殊部队|木叶暗部", "black_ops_unit", "varies", "hatake_kakashi|yamato|uchiha_itachi", "masks|coded_orders|assassination|intel_retrieval", "active_roster|mission_classification|chain_of_command|casualties", "暗部不是万能警察；任务保密、授权链和死亡率必须体现。"),
    ("academy", "忍者学校", "忍校|木叶忍者学校", "training_institution", "varies", "iruka|mizuki|sarutobi_konohamaru", "basic_jutsu_training|graduation_exam|team_assignment", "student_roster|graduation_results|teacher_assignments|forbidden_scroll_security", "忍校阶段不能提前塞太多高阶忍术，否则毕业考试和下忍任务体系会失效。"),
    ("hyuga_clan", "日向一族", "日向家|白眼一族", "konoha_clan", "land_of_fire", "hyuga_hinata|hyuga_neji|hyuga_hiashi|hyuga_hanabi", "byakugan|gentle_fist|main_branch_side_branch_system", "main_branch_status|side_branch_curse_seal|heir_pressure|cloud_relation", "日向线的痛点是制度和家族义务，不要只写成父女误会。"),
    ("sound_four", "音忍四人众", "音忍五人众|音忍四人组", "elite_guard_team", "otogakure", "tayuya|kidomaru|jirobo|sakon_ukon|kimimaro", "curse_mark_stage_2|barrier_ninjutsu|sasuke_escort", "member_status|curse_mark_stage|sasuke_delivery_status|konoha_pursuers", "音忍四人众是佐助叛逃事件的路由器，改动会连锁改变木叶追击战。"),
    ("team_hebi", "蛇小队", "蛇|Hebi", "rogue_team", "none", "uchiha_sasuke|suigetsu|karin|jugo", "anti_itachi_objective|orochimaru_hideouts|specialist_members", "team_name|objective|member_loyalty|orochimaru_status", "蛇小队目标是找鼬，不能提前套用鹰小队的复仇木叶逻辑。"),
    ("otogakure", "音隐村", "音忍村|音隐", "hidden_village_minor", "land_of_sound_or_hidden_bases", "orochimaru|kabuto|sound_four|kimimaro", "curse_mark_experiments|human_labs|hidden_bases", "base_locations|experiment_subjects|orochimaru_body_status|alliance_with_suna", "音隐更像大蛇丸实验网络，不应写成制度完整的大国忍村。"),
    ("takigakure", "泷隐村", "泷隐", "hidden_village_minor", "land_of_waterfall", "fu|kakuzu", "seven_tails_history|waterfall_defense", "nanabi_status|village_security|kakuzu_history", "泷隐拥有七尾历史却不是五大村，适合表现小国持有战略资源的压力。"),
    ("land_of_iron_samurai", "铁之国武士", "铁之国|武士", "samurai_state", "land_of_iron", "mifune", "samurai_chakra_blades|neutral_summit_host|iaido", "neutrality_status|summit_security|samurai_mobilization", "铁之国不是忍村，政治中立和武士战法要与忍者体系区分。"),
    ("mount_myoboku", "妙木山", "蛤蟆山|妙木山蛤蟆", "summon_realm", "summon_world", "gamabunta|fukasaku|shima", "toad_contract|sage_mode_training|prophecy", "contract_holders|sage_training_status|summon_availability", "妙木山进入和仙术训练都要有媒介、时间与风险，不是随便刷副本。"),
    ("ryuchi_cave", "龙地洞", "蛇仙地|龙地洞蛇", "summon_realm", "summon_world", "manda|orochimaru|yakushi_kabuto", "snake_contract|senjutsu_variant", "contract_holders|snake_summons|sage_training_status", "龙地洞仙术线偏危险研究与蛇系契约，不应和妙木山完全同质化。"),
    ("shikkotsu_forest", "湿骨林", "蛞蝓圣地", "summon_realm", "summon_world", "katsuyu|tsunade|haruno_sakura", "slug_contract|medical_support", "contract_holders|katsuyu_split_ratio|healing_chakra_supply", "蛞蝓治疗强度由召唤者查克拉供给决定，不能无限分裂无限治疗。"),
]


def tool(record: tuple[str, ...]) -> dict[str, Any]:
    record_id, name_zh, aliases, type_name, abilities, rule = record
    return {
        "id": record_id,
        "name_zh": name_zh,
        "aliases": parts(aliases),
        "type": type_name,
        "owner_history": [],
        "abilities": parts(abilities),
        "continuity_rule": rule,
    }


TOOL_ROWS = [
    ("kunai", "苦无", "苦无刀", "standard_weapon", "melee|throwing|trap_anchor", "苦无是通用忍具，可用于格挡、投掷、挂起爆符，但数量和携带位置应合理。"),
    ("shuriken", "手里剑", "忍者镖", "standard_weapon", "throwing|distraction|wire_combo", "手里剑适合牵制和试探，不应轻易击杀上忍级目标。"),
    ("explosive_tag", "起爆符", "爆符|引爆符", "consumable_explosive", "delayed_explosion|trap|area_denial", "起爆符是消耗品，必须记录库存、布置时间和引爆方式。"),
    ("smoke_bomb", "烟雾弹", "烟幕弹", "consumable_tool", "line_of_sight_block|escape_cover", "烟雾会阻断视线，但对白眼、嗅觉、感知和风遁未必有效。"),
    ("flash_bomb", "闪光弹", "闪光玉", "consumable_tool", "visual_disruption|escape_cover", "闪光适合干扰瞳术视线，但对闭眼感知或非视觉定位效果有限。"),
    ("soldier_pill", "兵粮丸", "兵粮药", "consumable_medicine", "temporary_stamina_restore|chakra_support", "兵粮丸是短期补给，不能代替休息；过量使用应有副作用。"),
    ("forehead_protector", "护额", "忍者护额", "identity_marker", "village_identity|rank_milestone_symbol", "护额代表忍者身份、叛忍划痕和阵营归属，毕业/叛逃/投诚时要记录变化。"),
    ("storage_scroll", "封物卷轴", "储物卷轴|忍具卷轴", "seal_medium", "item_storage|weapon_deployment", "卷轴可储物但需封印术式和查克拉启动，容量与内容要登记。"),
    ("summoning_scroll", "通灵卷轴", "契约卷轴", "contract_medium", "summon_contract_record|blood_contract", "通灵卷轴承载契约血印，签约、传承和丢失都会改变召唤资格。"),
    ("wire_string", "钢丝", "忍线|金属丝", "trap_tool", "trap|weapon_guidance|binding", "钢丝可配合手里剑和火遁，但布置需要时间、角度和遮蔽。"),
    ("senbon", "千本", "针", "precision_weapon", "pressure_point_attack|fake_death_setup|medical_use", "千本可造成假死/穴位效果，但需要解剖知识和命中精度。"),
    ("chakra_blade", "查克拉刀", "查克拉短刀", "chakra_conductive_weapon", "chakra_flow|nature_channeling", "查克拉刀需材料和属性控制，不能让所有角色随便灌属性。"),
]


def lore(record: tuple[str, ...]) -> dict[str, Any]:
    record_id, name_zh, aliases, category, summary, rules, story_use = record
    return {
        "id": record_id,
        "name_zh": name_zh,
        "aliases": parts(aliases),
        "category": category,
        "summary": summary,
        "continuity_rules": parts(rules),
        "story_use": story_use,
    }


LORE_ROWS = [
    ("mission_rank_system", "任务等级制度", "D级任务|C级任务|B级任务|A级任务|S级任务", "mission_economy", "忍村通过委托任务维持经济与政治影响力。任务等级大体对应风险、报酬、保密程度和派遣忍者级别。", "下忍常规从 D/C 级起步；越级任务必须有误报、护卫升级或战局突变。|S 级任务通常涉及国家、影级人物、叛忍或战争风险。", "给日常章和主线章分配合理风险，避免第 1 卷就把下忍长期扔进影级任务。"),
    ("shinobi_rank_system", "忍者等级体系", "忍者学校学生|下忍|中忍|上忍|特别上忍|影", "rank_and_office", "等级代表职责和平均能力，但战斗结果还受情报、血继、地形、配合、查克拉和心理状态影响。", "低等级越级胜利需要战术、克制或外部条件。|中忍更强调判断和指挥，上忍更强调综合实力与任务独立性。", "写升级、考试和带队资格时，用等级约束任务权责。"),
    ("chakra_core_mechanics", "查克拉核心机制", "查克拉|身体能量|精神能量", "power_system", "查克拉来自身体能量与精神能量的提炼和混合，是忍术、幻术、医疗、封印和部分体术强化的底层资源。", "大术要写消耗、控制和恢复。|精神打击、伤病、封印和疲劳会影响提炼效率。", "每场战斗后更新角色查克拉百分比、伤势和冷却。"),
    ("nature_transformation_system", "查克拉性质变化", "火风雷土水|性质变化|属性查克拉", "power_system", "五大性质变化影响忍术属性、克制与修炼门槛；血继或高级遁术常涉及性质组合或特殊体质。", "角色不能无训练突然全属性精通。|属性克制是战术变量，不是绝对胜负公式。", "设计训练线和战斗克制时，用属性限制降低外挂感。"),
    ("shape_transformation_system", "查克拉形态变化", "形态变化|查克拉控制", "power_system", "形态变化决定查克拉的形状、旋转、压缩和延展，螺旋丸等术尤其依赖高精度控制。", "形态变化训练可以分阶段写。|控制失败应体现为散逸、反伤、威力不足或维持时间短。", "用训练阶段填充章节，而不是靠心理独白注水。"),
    ("kekkei_genkai_system", "血继限界体系", "血继限界|血继淘汰|秘传", "power_system", "血继通常来自遗传、体质或特殊移植，不应被普通修炼无代价复制；秘传术则多由家族传承和训练掌握。", "血继和秘传要分清。|移植获得能力必须记录来源、适配、排异、查克拉负担和政治风险。", "防止主角随手捡血继，维持成长曲线和家族政治压力。"),
    ("dojutsu_registry_rule", "瞳术登记规则", "写轮眼|白眼|轮回眼|万花筒", "continuity_tracking", "瞳术牵涉眼位、来源、开眼阶段、移植适配、视力恶化和知情范围，必须作为身体部位和秘密资产追踪。", "每只眼单独记录左/右、原主人、现主人、阶段和损耗。|瞳术暴露会引发追杀、政治谈判或夺眼行动。", "写卡卡西、带土、团藏、青等移植眼角色时防崩。"),
    ("jinchuriki_social_rule", "人柱力社会规则", "人柱力|尾兽容器", "tailed_beast", "人柱力既是军事威慑也是社会排斥对象，不同村子对其控制、保护、恐惧和利用方式不同。", "尾兽抽离通常导致宿主死亡或濒死。|完美人柱力需要长期关系与控制训练，不能一步到位。", "写鸣人、我爱罗、奇拉比等角色时，用村内舆论和军事价值制造真实压力。"),
    ("summon_contract_rule", "通灵契约规则", "通灵兽|契约兽|三大圣地", "summoning", "通灵依赖契约、查克拉和召唤者资格。大型通灵兽通常有自主性格和势力背景。", "签约来源必须清楚。|大型通灵不能当无代价战斗外挂或交通工具。", "通灵兽可增加战斗画面，但必须纳入库存和查克拉账。"),
    ("genjutsu_counterplay_rule", "幻术攻防规则", "幻术|解幻术", "power_system", "幻术影响感知和精神，常通过查克拉扰动、外部刺激、瞳术对抗或伙伴打断破解。", "幻术不是万能读心术。|强幻术应写触发条件、维持成本和破解窗口。", "让战斗有智斗空间，避免幻术一出直接跳结局。"),
    ("fuinjutsu_cost_rule", "封印术代价规则", "封印|封印式|封印卷轴", "power_system", "封印术依赖术式、媒介、查克拉精度和目标状态，高阶封印常与牺牲或长期准备绑定。", "每个封印都要写媒介、限制、解除条件。|尸鬼封尽、尾兽封印等不能作为普通封条处理。", "用于阻止“封印术万能钥匙”式崩坏。"),
    ("village_politics_rule", "忍村政治规则", "火影|风影|五影|顾问|大名", "geopolitics", "忍村是国家军事力量和任务经济核心，但大名、顾问、忍族、暗部、根部和民众都能影响决策。", "不要把村子写成单一意志。|影的命令也会受资源、舆论、外交和派系制衡。", "避免无脑黑木叶，也避免把火影写成万能独裁者。"),
    ("small_country_pressure_rule", "小国夹缝规则", "雨之国|草之国|泷隐|小国", "geopolitics", "小国常夹在大国战争和忍村任务经济之间，资源少、外交脆弱，容易成为战争代理场或实验场。", "小国剧情要体现大国压力和民生代价。|小国持有尾兽或秘术会带来更高战略风险。", "写雨隐、泷隐、草隐时增加现实压力，而不是只当地图名。"),
    ("team_composition_rule", "小队配置规则", "三人小队|带队上忍|侦察班|追踪班", "team_logic", "标准小队通常围绕职责互补配置，侦察、医疗、近战、控制和火力的组合会决定任务解法。", "侦察班会提前发现伏击。|缺医疗或感知会提高战损和误判。", "根据队伍功能设计事件，而不是让所有队伍用同一种打法。"),
    ("knowledge_boundary_rule", "秘密知情边界", "知情范围|秘密|情报边界", "continuity_tracking", "角色只能根据已知情报做选择。带土身份、鼬真相、佩恩本体、月之眼计划等秘密必须逐人记录。", "不能让角色凭作者视角行动。|秘密泄露要产生可信来源和后果。", "长篇防崩最重要的状态表之一。"),
    ("anime_expansion_policy", "动画扩展采用规则", "动画原创|漫画主线|扩展剧情", "canon_policy", "部分人物、任务和尾兽捕获细节在动画中有扩展。采用前应标注来源层级，避免与漫画主线锚点冲突。", "采用动画扩展要写进 story_graph 的 canon_layer。|若扩展与主线冲突，以本书设定优先并记录替代规则。", "给长篇补素材，同时避免读者质疑设定来源。"),
]


DATA_QUALITY_NOTES = [
    {
        "id": "enrichment_2026_04_14_world_and_midlayer",
        "category": "enrichment",
        "source_urls": SOURCE_URLS,
        "summary": "补充长篇写作中高频使用的中层资料：任务/等级/查克拉/血继/通灵/封印/小队配置/政治规则、标准忍具、补充角色、组织和忍术。",
        "policy": SOURCE_POLICY,
    }
]


PATCHES = [
    ("characters.json", "characters", [character(row) for row in CHARACTER_ROWS]),
    ("jutsus.json", "jutsus", [jutsu(row) for row in JUTSU_ROWS]),
    ("organizations.json", "organizations", [organization(row) for row in ORGANIZATION_ROWS]),
    ("artifacts.json", "standard_tools", [tool(row) for row in TOOL_ROWS]),
    ("world_background.json", "lore_entries", [lore(row) for row in LORE_ROWS]),
    ("data_quality_report.json", "enrichment_notes", DATA_QUALITY_NOTES),
]


def enrich_db(db_root: Path) -> dict[str, int]:
    if not db_root.exists():
        raise FileNotFoundError(f"资料库目录不存在: {db_root}")

    summary: dict[str, int] = {}
    for file_name, collection_name, records in PATCHES:
        path = db_root / file_name
        data = load_json(path)
        ensure_source(data)
        added = merge_records(data, collection_name, records)
        write_json(path, data)
        summary[f"{file_name}:{collection_name}"] = added
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="补充 Naruto Author 资料库的世界观、人物、忍术、组织和忍具锚点")
    parser.add_argument(
        "--db",
        dest="db_roots",
        action="append",
        required=True,
        help="要补充的 naruto_fanfic_db 目录；可重复传入以同步 skill 内置库和项目库",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for raw_db_root in args.db_roots:
        db_root = Path(raw_db_root).resolve()
        summary = enrich_db(db_root)
        print(f"[OK] 已补充资料库: {db_root}")
        for key, added in summary.items():
            print(f"  - {key}: 新增 {added} 条")
    return 0


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
