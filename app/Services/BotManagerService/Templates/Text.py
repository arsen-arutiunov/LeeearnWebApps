class Text:
    @staticmethod
    def _format_template(template: str, args: tuple) -> str:
        """
        Універсальна функція для підстановки значень у шаблон.

        :param template: Текст із плейсхолдерами.
        :param args: Аргументи для підстановки у шаблон.
        :return: Відформатований текст.
        """
        import re

        def get_value(index: int):
            try:
                return str(args[index])
            except IndexError:
                raise ValueError(f"Значення для плейсхолдера <{index}> не знайдено в аргументах.")

        # Знаходимо всі плейсхолдери <0>, <1>, ...
        pattern = r"<(\d+)>"
        placeholders = re.findall(pattern, template)

        # Замінюємо плейсхолдери
        for placeholder in placeholders:
            index = int(placeholder)
            value = get_value(index)
            template = template.replace(f"<{placeholder}>", value)

        return template

    @staticmethod
    async def start_success_teacher(*args):
        template = "Привіт <0> Ти увійшов як <b><1></b>.\n\nЯ твій особистий помічник вчителя. Чим буду корисний?"
        return Text._format_template(template, args)


    @staticmethod
    async def start_error_notfound(*args):
        template = "❌ Ви не маєте доступу до боту."
        return Text._format_template(template, args)