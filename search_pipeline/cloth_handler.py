MIN_CLOTHES_SIZE_INT = 18
MAX_CLOTHES_SIZE_INT = 82
MIN_CHILD_CLOTHES_SIZE_INT = MIN_CLOTHES_SIZE_INT
MAX_CHILD_CLOTHES_SIZE_INT = 43
MIN_W_SCHOOL_CLOTHES_SIZE_INT = 26
MAX_W_SCHOOL_CLOTHES_SIZE_INT = 48
MIN_M_SCHOOL_CLOTHES_SIZE_INT = 28
MAX_M_SCHOOL_CLOTHES_SIZE_INT = 50
MAX_CLOTHES_SIZE_X_COUNT = 12


class ClothFact:

    class Gender:
        MAN = 1
        WOMAN = 2
        UNISEX = 3

    class Season:
        DEMI_SEASON = 1
        WINTER = 2
        SUMMER = 3

    def __init__(self, class_name, parsed_name, size_info, prop_dict):
        self.class_name = class_name
        self.parsed_name = parsed_name
        self.size_info = size_info
        self.props = prop_dict.copy()
        self.parsed_size_info = None
        self.decode_size_info()

    @staticmethod
    def _is_size_letters(token):
        res = True
        first_digits = []
        letters_started = False
        end_letter_reached = False
        x_count = 0
        for c in token:
            if end_letter_reached:
                res = False
                break
            if c.isdigit():
                if letters_started:
                    res = False
                    break
                first_digits.append(c)
                continue
            if not letters_started:
                if len(first_digits) > 0:
                    if c.lower() != "x":
                        res = False
                        break
                    digit_val = int("".join(first_digits))
                    if digit_val < 1 or digit_val > MAX_CLOTHES_SIZE_X_COUNT:
                        res = False
                        break
                if c.lower() not in ["x", "s", "m", "l"]:
                    res = False
                    break
                if c.lower() in ["s", "m", "l"]:
                    end_letter_reached = True
                first_digits = []
                letters_started = True
                continue
            if c.lower() == "x":
                x_count += 1
                if len(first_digits) > 0 or x_count > MAX_CLOTHES_SIZE_X_COUNT:
                    res = False
                    break
                continue
            if c.lower() not in ["s", "m", "l"]:
                res = False
                break
            end_letter_reached = True
        if not letters_started or not end_letter_reached:
            res = False
        return res

    @staticmethod
    def _size_letter_toks_to_value(size_letters, gender, max_x_count):

        def lead_number_to_x(size_info, max_x_count):
            first_digits = []
            res = []
            for pos, c in enumerate(size_info):
                if c.isdigit():
                    first_digits.append(c)
                    continue
                if len(first_digits) > 0:
                    digit_val = max(1, min(int("".join(first_digits)), max_x_count))
                    res = "".join(["x"] * digit_val)
                    if c.lower() != "x":
                        res += size_info[pos:]
                    else:
                        res += size_info[pos + 1:]
                else:
                    res = size_info
                break
            return res.lower()

        def letters_to_range(letters, gender_code):
            m_letters_to_size_map = {
                "xs": (40, 44),
                "s": (42, 48),
                "m": (44, 50),
                "l": (48, 52),
                "xl": (50, 56),
                "xxl": (52, 60),
                "xxxl": (54, 64),
                "xxxxl": (56, 66),
                "xxxxxl": (58, 70),
                "xxxxxxl": (60, 72),
                "xxxxxxxl": (62, 74),
                "xxxxxxxxl": (64, 76),
                "xxxxxxxxxl": (66, 78),
                "xxxxxxxxxxl": (68, 80),
            }
            w_letters_to_size_map = {
                "xxxs": (36, 36),
                "xxs": (38, 38),
                "xs": (38, 44),
                "s": (42, 46),
                "m": (44, 48),
                "l": (46, 50),
                "xl": (48, 54),
                "xxl": (50, 58),
                "xxxl": (52, 64),
                "xxxxl": (54, 66),
                "xxxxxl": (56, 70),
                "xxxxxxl": (58, 74),
                "xxxxxxxl": (56, 78),
                "xxxxxxxxl": (58, 82),
            }

            if gender_code == "m":
                mapper = m_letters_to_size_map
            else:
                mapper = w_letters_to_size_map

            if letters not in mapper:
                if letters[-1] == "l":
                    res_range = (max(max(v) for v in mapper.values()), MAX_CLOTHES_SIZE_INT)
                else:
                    res_range = (MIN_CLOTHES_SIZE_INT, min(min(v) for v in mapper.values()))
            else:
                res_range = mapper[letters]

            assert res_range[0] <= res_range[1]
            return res_range

        size_letters = lead_number_to_x(size_letters, max_x_count)

        if gender is None or gender == ClothFact.Gender.UNISEX:
            m_range = letters_to_range(size_letters, "m")
            w_range = letters_to_range(size_letters, "w")
            size_range = (min(m_range[0], w_range[0]), max(m_range[1], w_range[1]))
        elif gender == ClothFact.Gender.MAN:
            size_range = letters_to_range(size_letters, "m")
        elif gender == ClothFact.Gender.WOMAN:
            size_range = letters_to_range(size_letters, "w")
        else:
            raise ValueError(f"Unknown gender value: {gender}")

        return size_range

    def decode_size_info(self):

        def direct_info_to_range(fact, gender):

            def _number_toks_to_value(number_info):
                if number_info.frac_part is not None:
                    res = float(f"{number_info.int_part}.{number_info.frac_part}")
                else:
                    res = int(number_info.int_part)
                return res

            size_info = fact.direct_values
            info_type = size_info.__class__.__name__
            if info_type == "size_number_list":
                size_from = _number_toks_to_value(size_info.from_info)
                if size_info.to_info is None:
                    size_to = size_from
                else:
                    size_to = _number_toks_to_value(size_info.to_info)
                size_range = (size_from, size_to)
            elif info_type == "size_letters_list":
                range_from = ClothFact._size_letter_toks_to_value(size_info.from_info.letters, gender, MAX_CLOTHES_SIZE_X_COUNT)
                if size_info.to_info is None:
                    range_to = range_from
                else:
                    range_to = ClothFact._size_letter_toks_to_value(size_info.to_info.letters, gender, MAX_CLOTHES_SIZE_X_COUNT)
                size_range = (min(range_from), max(range_to))
            else:
                raise ValueError(f"Unknown info type \"{info_type}\"")

            return size_range

        def indirect_info_to_range(size_info, self):
            if size_info.keyword == "мальчик":
                self.props["gender"] = ClothFact.Gender.MAN
                size_range = (MIN_CHILD_CLOTHES_SIZE_INT, MAX_CHILD_CLOTHES_SIZE_INT)
            elif size_info.keyword == "девочка":
                self.props["gender"] = ClothFact.Gender.WOMAN
                size_range = (MIN_CHILD_CLOTHES_SIZE_INT, MAX_CHILD_CLOTHES_SIZE_INT)
            elif size_info.keyword == "мужчина":
                self.props["gender"] = ClothFact.Gender.MAN
                size_range = (MAX_CHILD_CLOTHES_SIZE_INT, MAX_CLOTHES_SIZE_INT)
            elif size_info.keyword == "женщина":
                self.props["gender"] = ClothFact.Gender.WOMAN
                size_range = (MAX_CHILD_CLOTHES_SIZE_INT, MAX_CLOTHES_SIZE_INT)
            elif size_info.keyword == "ребёнок":
                size_range = (MIN_CLOTHES_SIZE_INT, MAX_CHILD_CLOTHES_SIZE_INT)
            elif size_info.keyword == "взрослый":
                size_range = (MAX_CHILD_CLOTHES_SIZE_INT, MAX_CLOTHES_SIZE_INT)
            elif size_info.keyword == "школьник":
                # in some cases this word can also be applicable to women
                if "gender" not in self.props or self.props["gender"] is None:
                    self.props["gender"] = ClothFact.Gender.MAN
                size_range = (MIN_M_SCHOOL_CLOTHES_SIZE_INT, MAX_M_SCHOOL_CLOTHES_SIZE_INT)
            elif size_info.keyword == "школьница":
                self.props["gender"] = ClothFact.Gender.WOMAN
                size_range = (MIN_W_SCHOOL_CLOTHES_SIZE_INT, MAX_W_SCHOOL_CLOTHES_SIZE_INT)
            else:
                raise ValueError(f"Unknown keyword: {size_info.keyword}")

            if size_info.year_info_from_y is not None:
                year_to_size_map = {
                    0: (18, 26),
                    1: (26, 28),
                    2: (28, 30),
                    3: (28, 30),
                    4: (30, 30),
                    5: (30, 32),
                    6: (32, 34),
                    7: (34, 36),
                    8: (34, 36),
                    9: (36, 36),
                    10: (36, 36),
                    11: (36, 38),
                    12: (36, 38),
                    13: (38, 40),
                    14: (38, 40),
                }
                if size_info.year_info_to_y is None:
                    size_info.year_info_to_y = size_info.year_info_from_y
                from_y = int(size_info.year_info_from_y)
                to_y = int(size_info.year_info_to_y)

                size_from = year_to_size_map.get(from_y, (MAX_CHILD_CLOTHES_SIZE_INT, size_range[1]))
                size_to = year_to_size_map.get(to_y, (size_range[0], MAX_CLOTHES_SIZE_INT))
                size_range = (min(size_from), max(size_to))
            elif size_info.year_info_from_m is not None:
                month_to_size_map = {
                    0: (18, 18),
                    1: (18, 20),
                    2: (18, 20),
                    3: (18, 22),
                    4: (20, 22),
                    5: (20, 22),
                    6: (20, 24),
                    7: (22, 24),
                    8: (22, 24),
                    9: (22, 26),
                    10: (24, 26),
                    11: (24, 26),
                    12: (24, 26),
                }
                if size_info.year_info_to_m is None:
                    size_info.year_info_to_m = size_info.year_info_from_m
                from_m = int(size_info.year_info_from_m)
                to_m = int(size_info.year_info_to_m)

                size_from = month_to_size_map.get(from_m, (MAX_CHILD_CLOTHES_SIZE_INT, size_range[1]))
                size_to = month_to_size_map.get(to_m, (size_range[0], MAX_CLOTHES_SIZE_INT))
                size_range = (min(size_from), max(size_to))
            else:
                # no info is present
                pass

            return size_range

        if self.size_info is None:
            return

        obj_class_name = self.size_info.__class__.__name__
        if obj_class_name == "size_info":
            if self.size_info.direct_values is not None:
                size_range = direct_info_to_range(self.size_info.direct_values, self.props.get("gender", None))
            elif self.size_info.indirect_values is not None:
                size_range = indirect_info_to_range(self.size_info.indirect_values, self)
            else:
                raise ValueError("Both size infos are None, while object itself is not")
        else:
            raise ValueError(f"No handler for object \"{obj_class_name}\"")

        if size_range[0] > size_range[1]:
            size_range = (size_range[1], size_range[0])

        self.parsed_size_info = size_range
        assert isinstance(self.parsed_size_info, tuple) and len(self.parsed_size_info) == 2

    def __str__(self):
        return str(self.__dict__)
