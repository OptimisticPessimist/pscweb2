import yaml
from production.models import Production
from rehearsal.models import Character, Scene, Appearance
from ..fountain import fountain
from ..models import Script


def data_from_sp_yaml(text):
    """sp.yaml フォーマットの台本からデータを取得"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return [], [], []

    # dataがNoneや辞書でない場合に対応
    if not isinstance(data, dict):
        return [], [], []

    meta = data.get("meta", {})

    # 登場人物の別名を本名に変換するためのマップを作成
    alias_to_main_name_map = {}
    if 'characters' in data and isinstance(data.get('characters'), list):
        for char_data in data.get('characters', []):
            main_name = char_data.get('name')
            if not main_name:
                continue
            # 本名自身もマップに追加
            alias_to_main_name_map[main_name] = main_name
            # 別名をマップに追加
            for alias in char_data.get('alias', []):
                alias_to_main_name_map[alias] = main_name

    # 実際にセリフを話した登場人物を抽出しながらデータを生成
    characters = []
    scenes = []
    appearance = []
    for scene_data in data.get('scenes', []):
        scene_name = scene_data.get('name', '無題のシーン')
        scenes.append(scene_name)

        # セリフ数をカウントして出番データを作成
        scn_apprs = {}
        body = scene_data.get('body', '')
        if body:
            for line in body.splitlines():
                if ':' in line:
                    speaker, _ = line.split(':', 1)
                    speaker = speaker.strip()

                    # 別名マップを使って本名に正規化。マップにない場合は speaker 自身を本名とみなす
                    main_name = alias_to_main_name_map.get(speaker, speaker)

                    # 登場人物リストに登場順で追加 (重複は避ける)
                    if main_name not in characters:
                        characters.append(main_name)

                    # セリフ数をカウント
                    scn_apprs[main_name] = scn_apprs.get(main_name, 0) + 1
        appearance.append(scn_apprs)

    return meta, characters, scenes, appearance


def html_from_sp_yaml(text):
    """sp.yaml フォーマットの台本から HTML を生成"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        return f"<h1>YAML Parse Error</h1><p>{e}</p>"

    # dataがNoneや辞書でない場合に対応
    if not isinstance(data, dict):
        data = {}

    # メタデータからHTMLヘッダを生成
    meta = data.get('meta', {})
    content = f"<h1>{meta.get('title', '無題')}</h1>"
    content += f"<div style='text-align:right;'>{meta.get('author', '作者不明')}</div>"
    content += "<hr>"

    # シーンごとにHTMLを生成
    for scene_data in data.get('scenes', []):
        content += f"<h2>{scene_data.get('name', '無題のシーン')}</h2>"
        body = scene_data.get('body', '')
        if body:
            for line in body.splitlines():
                line = line.strip()
                if ':' in line:
                    char_name, dialogue = line.split(':', 1)
                    content += f"<p><strong>{char_name.strip()}:</strong>{dialogue.strip()}</p>"
                elif line.startswith('(') and line.endswith(')'):
                    content += f"<p style='margin-left: 2em; color: gray;'>{line}</p>"
                else:
                    content += f"<p>{line}</p>"
        content += "<br>"

    # HTML全体を組み立てる
    html = f"""<html lang="ja">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
        </head>
        <body>{content}</body>
    </html>"""
    return html


def add_data_from_script(prod_id, scrpt_id):
    '''台本を元に公演にシーン、登場人物、出番を追加する
    '''
    # データを追加する公演
    production = Production.objects.filter(pk=prod_id).first()
    if not production:
        return

    # 台本データを取得
    script = Script.objects.filter(pk=scrpt_id).first()
    if not script:
        return

    # 既存のシーン、登場人物、出番データを削除
    # 外部キー制約のため、関連するモデルから先に削除
    Appearance.objects.filter(scene__production=production).delete()
    Scene.objects.filter(production=production).delete()
    Character.objects.filter(production=production).delete()

    # 台本のフォーマットに応じてデータを取得
    if script.format == 1:  # Fountain
        meta, characters, scenes, appearance = data_from_fountain(script.raw_data)
    elif script.format == 2:  # sp.yaml
        meta, characters, scenes, appearance = data_from_sp_yaml(script.raw_data)
    else:
        return

    # 登場人物を追加しながらインスタンスを記録する
    char_instances = {}
    for idx, char_name in enumerate(characters):
        character = Character(production=production,
                              name=char_name, sortkey=idx)
        character.save()
        char_instances[char_name] = character

    # シーンと出番を追加 (★バグ修正：ループのネストを解消)
    for idx, scene_name in enumerate(scenes):
        # 出番のセリフ数の合計を出しておく
        scn_appr = appearance[idx]
        scn_lines_num = sum(scn_appr.values())
        # インスタンス生成、保存
        scene = Scene(
            production=production,
            name=scene_name,
            sortkey=idx,
            length=scn_lines_num,
            length_auto=True,
        )
        scene.save()
        # 出番の追加
        for char_name, lines_num in scn_appr.items():
            # 登場人物が char_instances に存在する場合のみ出番を作成
            if char_name in char_instances:
                appr = Appearance(
                    scene=scene,
                    character=char_instances[char_name],
                    lines_num=lines_num,
                    lines_auto=True,
                )
                appr.save()


def data_from_fountain(text):
    '''Fountain フォーマットの台本からデータを取得
    '''
    f = fountain.Fountain(string=text)

    # ★修正: メタデータを取得し、sp.yamlの形式に合わせる
    meta = {}
    for key, value in f.metadata.items():
        if value:
            meta[key] = value[0]

    characters = []
    scenes = []
    appearance = []
    scn_apprs = {}

    for e in f.elements:
        if e.element_type == 'Character':
            if scenes:
                char_name = e.element_text
                current_count = scn_apprs.get(char_name, 0)
                scn_apprs[char_name] = current_count + 1
                if char_name not in characters:
                    characters.append(char_name)
            continue
        if e.element_type in ('Scene Heading', 'Section Heading'):
            if scenes:
                if scenes[-1] == '登場人物':
                    scenes.pop()
                else:
                    appearance.append(scn_apprs)
                scn_apprs = {}
            scenes.append(e.element_text)

    if scenes:
        if scenes[-1] == '登場人物':
            scenes.pop()
        else:
            appearance.append(scn_apprs)

    # ★修正: metaを戻り値に追加
    return meta, characters, scenes, appearance


def html_from_fountain(text):
    '''Fountain フォーマットの台本から HTML を生成
    '''
    f = fountain.Fountain(string=text)
    content = ''
    if 'title' in f.metadata:
        for title in f.metadata['title']:
            content += f'<h1>{title}</h1>'
    if 'author' in f.metadata:
        for author in f.metadata['author']:
            content += f'<div style="text-align:right;">{author}</div>'
    content += '<hr>'

    for e in f.elements:
        if e.element_type == 'Scene Heading':
            content += f'<h2>{e.element_text}</h2>'
        elif e.element_type == 'Action':
            if e.is_centered:
                content += f'<p style="text-align:center;">{e.element_text}</p>'
            else:
                content += f'<p>{e.element_text}</p>'
        elif e.element_type == 'Character':
            content += f'<p><strong>{e.element_text}</strong></p>'
        elif e.element_type == 'Dialogue':
            dialogue_html = e.element_text.replace('\n', '<br>')
            content += f'<div style="margin-left: 2em;">{dialogue_html}</div>'
        elif e.element_type == 'Parenthetical':
            content += f'<div style="margin-left: 2em; color: gray;">{e.element_text}</div>'
        elif e.element_type == 'Transition':
            content += f'<p style="text-align: right;"><em>{e.element_text.upper()}</em></p>'
        elif e.element_type == 'Section Heading':
            content += f'<h3 style="margin-top: 2em;">{e.element_text}</h3>'
        elif e.element_type == 'Page Break':
            content += '<hr style="margin: 2em 0;">'
        elif e.element_type == 'Empty Line':
            content += '<br>'
        # Synopsis, Comment, Boneyard はビューアでは無視

    html = f"""<html lang="ja">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
            <style>
                body {{ line-height: 1.6; font-family: sans-serif; }}
                h1, h2, h3 {{ margin-top: 1.5em; margin-bottom: 0.5em; }}
                p {{ margin: 0.5em 0; }}
            </style>
        </head>
        <body>{content}</body>
    </html>"""
    return html
