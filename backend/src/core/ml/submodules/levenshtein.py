from typing import List, Tuple, Optional, Dict, Any
from ...services.applogger import Logger
from ...base.utils import Utils


class LevenshteinCalculator:
    """
    Калькулятор расстояния Левенштейна для нечеткого поиска и сравнения строк.
    
    Предоставляет методы для:
    - Вычисления расстояния Левенштейна между строками
    - Определения схожести строк (0.0 - 1.0)
    - Нечеткого поиска по коллекции строк
    - Исправления опечаток с использованием словаря
    
    Example:
        >>> calculator = LevenshteinCalculator(logger=logger, threshold=0.7)
        >>> distance = calculator.calculate_distance("привет", "превет")
        >>> similarity = calculator.calculate_similarity("тест", "test")
        >>> best_match = calculator.find_best_match("контракт", ["контракты", "договор", "соглашение"])
    """
    
    def __init__(self, logger: Optional[Logger] = None, threshold: float = 0.6):
        """
        Инициализация калькулятора Левенштейна
        
        Args:
            logger (Optional[Logger]): Логгер для записи операций
            threshold (float): Минимальный порог схожести для совпадений (0.0 - 1.0)
        """
        self.logger = logger
        self.threshold = max(0.0, min(1.0, threshold))
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message=f"{self.__class__.__name__} инициализирован с порогом {self.threshold}"
        )
    
    def calculate_distance(self, s1: str, s2: str, case_sensitive: bool = False) -> int:
        """
        Вычисляет расстояние Левенштейна между двумя строками
        
        Args:
            s1 (str): Первая строка
            s2 (str): Вторая строка
            case_sensitive (bool): Учитывать ли регистр символов
            
        Returns:
            int: Расстояние Левенштейна (количество операций редактирования)
            
        Example:
            >>> calculator.calculate_distance("привет", "превет")
            1
            >>> calculator.calculate_distance("кот", "код")
            1
        """
        try:
            # Нормализация строк
            str1 = s1 if case_sensitive else s1.lower()
            str2 = s2 if case_sensitive else s2.lower()
            
            # Оптимизация: если одна из строк пустая
            if not str1:
                return len(str2)
            if not str2:
                return len(str1)
            
            # Оптимизация: если строки равны
            if str1 == str2:
                return 0
            
            # Оптимизация: меняем строки местами для экономии памяти
            if len(str1) < len(str2):
                str1, str2 = str2, str1
            
            # Алгоритм Левенштейна с оптимизацией по памяти
            previous_row = list(range(len(str2) + 1))
            
            for i, c1 in enumerate(str1):
                current_row = [i + 1]
                for j, c2 in enumerate(str2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            distance = previous_row[-1]
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Расстояние Левенштейна между '{s1}' и '{s2}': {distance}"
            )
            
            return distance
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка вычисления расстояния Левенштейна: {e}"
            )
            raise
    
    def calculate_similarity(self, s1: str, s2: str, case_sensitive: bool = False) -> float:
        """
        Вычисляет схожесть строк на основе расстояния Левенштейна
        
        Args:
            s1 (str): Первая строка
            s2 (str): Вторая строка
            case_sensitive (bool): Учитывать ли регистр символов
            
        Returns:
            float: Коэффициент схожести от 0.0 (полностью разные) до 1.0 (идентичные)
            
        Example:
            >>> calculator.calculate_similarity("привет", "превет")
            0.8333333333333334
            >>> calculator.calculate_similarity("тест", "тест")
            1.0
        """
        try:
            distance = self.calculate_distance(s1, s2, case_sensitive)
            max_length = max(len(s1), len(s2))
            
            if max_length == 0:
                return 1.0
            
            similarity = 1.0 - (distance / max_length)
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Схожесть между '{s1}' и '{s2}': {similarity:.4f}"
            )
            
            return similarity
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка вычисления схожести: {e}"
            )
            raise
    
    def find_best_match(self, query: str, candidates: List[str], 
                       case_sensitive: bool = False) -> Tuple[Optional[str], float]:
        """
        Находит лучшее совпадение среди кандидатов
        
        Args:
            query (str): Поисковая строка
            candidates (List[str]): Список строк-кандидатов
            case_sensitive (bool): Учитывать ли регистр символов
            
        Returns:
            Tuple[Optional[str], float]: Лучшее совпадение и его коэффициент схожести
            
        Example:
            >>> candidates = ["контракт", "договор", "соглашение"]
            >>> match, score = calculator.find_best_match("контракты", candidates)
            >>> print(f"Найдено: {match} (схожесть: {score:.2f})")
        """
        try:
            if not candidates:
                Utils.writelog(
                    logger=self.logger,
                    level="WARNING",
                    message="Пустой список кандидатов для поиска"
                )
                return None, 0.0
            
            best_match = None
            best_score = 0.0
            
            for candidate in candidates:
                if not isinstance(candidate, str):
                    continue
                    
                similarity = self.calculate_similarity(query, candidate, case_sensitive)
                
                if similarity > best_score and similarity >= self.threshold:
                    best_score = similarity
                    best_match = candidate
            
            Utils.writelog(
                logger=self.logger,
                level="INFO" if best_match else "WARNING",
                message=f"Поиск '{query}': {'найдено' if best_match else 'не найдено'} "
                       f"{'(' + best_match + ', схожесть: ' + str(round(best_score, 4)) + ')' if best_match else ''}"
            )
            
            return best_match, best_score
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска лучшего совпадения: {e}"
            )
            raise
    
    def find_multiple_matches(self, query: str, candidates: List[str], 
                            limit: int = 5, case_sensitive: bool = False) -> List[Tuple[str, float]]:
        """
        Находит несколько лучших совпадений среди кандидатов
        
        Args:
            query (str): Поисковая строка
            candidates (List[str]): Список строк-кандидатов
            limit (int): Максимальное количество результатов
            case_sensitive (bool): Учитывать ли регистр символов
            
        Returns:
            List[Tuple[str, float]]: Список совпадений с коэффициентами схожести, отсортированный по убыванию схожести
            
        Example:
            >>> matches = calculator.find_multiple_matches("контракт", candidates, limit=3)
            >>> for match, score in matches:
            ...     print(f"{match}: {score:.2f}")
        """
        try:
            if not candidates:
                return []
            
            matches = []
            
            for candidate in candidates:
                if not isinstance(candidate, str):
                    continue
                    
                similarity = self.calculate_similarity(query, candidate, case_sensitive)
                
                if similarity >= self.threshold:
                    matches.append((candidate, similarity))
            
            # Сортируем по убыванию схожести
            matches.sort(key=lambda x: x[1], reverse=True)
            
            # Ограничиваем количество результатов
            results = matches[:limit]
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Поиск '{query}': найдено {len(results)} совпадений из {len(candidates)} кандидатов"
            )
            
            return results
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка поиска множественных совпадений: {e}"
            )
            raise
    
    def correct_text(self, text: str, dictionary: List[str], 
                    case_sensitive: bool = False) -> Dict[str, Any]:
        """
        Исправляет опечатки в тексте, используя словарь
        
        Args:
            text (str): Исходный текст
            dictionary (List[str]): Словарь для исправления
            case_sensitive (bool): Учитывать ли регистр символов
            
        Returns:
            Dict[str, Any]: Результат исправления с деталями
            
        Example:
            >>> result = calculator.correct_text("првет мир", ["привет", "мир"])
            >>> print(result['corrected_text'])
            'привет мир'
        """
        try:
            if not text or not dictionary:
                return {
                    'original_text': text,
                    'corrected_text': text,
                    'corrections': [],
                    'corrections_count': 0
                }
            
            words = text.split()
            corrected_words = []
            corrections = []
            
            for i, word in enumerate(words):
                best_match, score = self.find_best_match(word, dictionary, case_sensitive)
                
                if best_match and score > 0.7 and best_match != word:
                    corrected_words.append(best_match)
                    corrections.append({
                        'position': i,
                        'original': word,
                        'corrected': best_match,
                        'confidence': score
                    })
                else:
                    corrected_words.append(word)
            
            result = {
                'original_text': text,
                'corrected_text': ' '.join(corrected_words),
                'corrections': corrections,
                'corrections_count': len(corrections)
            }
            
            Utils.writelog(
                logger=self.logger,
                level="DEBUG",
                message=f"Исправление текста: {len(corrections)} исправлений из {len(words)} слов"
            )
            
            return result
            
        except Exception as e:
            Utils.writelog(
                logger=self.logger,
                level="ERROR",
                message=f"Ошибка исправления текста: {e}"
            )
            raise
    
    def set_threshold(self, new_threshold: float) -> None:
        """
        Устанавливает новый порог схожести
        
        Args:
            new_threshold (float): Новый порог (0.0 - 1.0)
        """
        old_threshold = self.threshold
        self.threshold = max(0.0, min(1.0, new_threshold))
        
        Utils.writelog(
            logger=self.logger,
            level="DEBUG",
            message=f"Порог схожести изменен с {old_threshold} на {self.threshold}"
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы калькулятора
        
        Returns:
            Dict[str, Any]: Статистическая информация
        """
        return {
            'threshold': self.threshold,
            'logger_enabled': self.logger is not None,
            'class_name': self.__class__.__name__
        }
