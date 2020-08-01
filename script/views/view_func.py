from production.models import Production
from rehearsal.models import Character, Scene, Appearance
from script.fountain import fountain
from script.models import Script


def add_data_from_script(prod_id, scrpt_id):
    '''台本を元に公演にシーン、登場人物、出番を追加する
    '''
    # 台本データを取得
    scripts = Script.objects.filter(pk=scrpt_id)
    if scripts.count() < 1:
        return
    script = scripts[0]
    
    # 台本データが Fountain フォーマットの場合のデータ取得
    if script.format == 1:
        characters, scenes, appearance = data_from_fountain(script.raw_data)
    else:
        return
    
    # データを追加する公演
    prods = Production.objects.filter(pk=prod_id)
    if prods.count() < 1:
        return
    production = prods[0]
    
    # 登場人物を追加しながらインスタンスを記録する
    char_instances = {}
    for idx, char_name in enumerate(characters):
        character = Character(production=production,
            name=char_name, sortkey=idx)
        character.save()
        char_instances[char_name] = character
    
    # シーンと出番を追加
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
            length_auto=False,
        )
        scene.save()
        # 出番の追加
        for char_name, lines_num in scn_appr.items():
            appr = Appearance(
                scene=scene,
                character=char_instances[char_name],
                lines_num=lines_num,
            )
            appr.save()


def data_from_fountain(text):
    '''Fountain フォーマットの台本からデータを取得
    
    Parameters
    ----------
    text : str
        台本のテキストデータ
    
    Returns
    -------
    characters : list
        Character 行から取得した登場人物名のリスト
    scenes : list
        Scene Heading 行または Section Heading 行から取得したシーン名のリスト
    appearance : list
        シーンごとの、出番 (dict) のリスト
    '''
    
    # パース
    f = fountain.Fountain(string=text)
    
    characters = []
    scenes = []
    appearance = []
    scn_apprs = {}
    
    for e in f.elements:
        # セリフ主の行
        if e.element_type == 'Character':
            # 少なくとも1個のシーンが検出されていれば
            if scenes:
                # 今のシーンのその人物のセリフ数を出番としてカウント
                char_name = e.element_text
                current_count = scn_apprs.get(char_name, 0)
                scn_apprs[char_name] = current_count + 1
                # 登場人物に登録
                if char_name not in characters:
                    characters.append(char_name)
            continue
        # シーン見出し
        if e.element_type in ('Scene Heading', 'Section Heading'):
            # 少なくとも1個のシーンが検出されていれば
            if scenes:
                # 今のシーンが「登場人物」なら、削除
                if scenes[-1] == '登場人物':
                    scenes.pop()
                else:
                    # ここまでの出番を今のシーンの出番とする
                    appearance.append(scn_apprs)
                # 出番をクリア
                scn_apprs = {}
            # 新しいシーンを追加
            scenes.append(e.element_text)
    
    # 最後のシーンの出番をセット
    if scenes:
        if scenes[-1] == '登場人物':
            scenes.pop()
        else:
            appearance.append(scn_apprs)
    
    return characters, scenes, appearance


def html_from_fountain(text):
    '''Fountain フォーマットの台本から HTML を生成
    
    Parameters
    ----------
    text : str
        台本のテキストデータ
    
    Returns
    -------
    html : str
        生成した HTML
    '''
    
    # パース
    f = fountain.Fountain(string=text)

    # コンテンツ生成
    content = ''
    # タイトル
    if 'title' in f.metadata:
        for title in f.metadata['title']:
            content += f'<h1>{title}</h1>'
    # 著者
    if 'author' in f.metadata:
        for author in f.metadata['author']:
            content += f'<div style="text-align:right;">{author}</div>'
    
    for e in f.elements:
        # 空行をスキップ
        if e.element_type == 'Empty Line':
            continue

        # 改行の処理をしたテキスト
        text = e.element_text.replace('\n', '<br>')
        
        # セリフ
        if e.element_type == 'Dialogue':
            line = f'<div style="margin-left:20;">{text}</div>'
        # ト書き
        elif e.element_type == 'Action':
            line = f'<div style="margin-left:40;">{text}</div>'
        elif e.element_type == 'Section Heading':
            line = f'<div style="font-weight:bold;">{text}</div>'
        # エンドマーク
        elif e.element_type == 'Transition':
            line = f'<div style="text-align:right;">{text}</div>'
        # その他
        else:
            line = f'<div>{text}</div>'
        
        # 直前に空行を入れるか
        insert_blank = False
        
        # セリフ主の前がセリフでなければ空行を挿入
        if e.element_type == 'Character' and last_type != 'Dialogue':
            insert_blank = True
        # ト書きの前がト書きでなければ空行を挿入
        elif e.element_type == 'Action' and last_type != 'Action':
            insert_blank = True
        # 柱なら空行を挿入
        elif e.element_type == 'Section Heading':
            insert_blank = True
        
        if insert_blank:
            line = '<div style="height:15"></div>' + line
        
        content += line
        last_type = e.element_type
    
    # HTML としての体裁を整える
    html = '<html lang="ja">'\
        '<head>'\
        '<meta charset="utf-8">'\
        '<meta name="viewport" content="width=device-width, '\
        'initial-scale=1.0, user-scalable=yes">'\
        '</head>'\
        '<body>' + content + '</body></html>'
    
    return html
