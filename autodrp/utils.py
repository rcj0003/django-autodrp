from django.db.models import Q
from functools import wraps
import inspect

from .checks import QueryBuilderCheck


class EvalArgument:
    def __init__(self, eval_string, *required_keywords):
        self._compiled_eval = compile(f'return {eval_string}', '<string>', 'eval')
        self.required_keywords = required_keywords
    
    def _validate_kwargs(self, kwargs):
        for keyword in self.required_keywords:
            if keyword not in kwargs:
                raise Exception(f'Missing keyword argument {keyword}.')

    def __call__(self, **kwargs):
        self._validate_kwargs(kwargs)
        return eval(self._compiled_eval, globals={}, locals=kwargs)

def _compile_and(q_obj=None, compiled_q=None, **kwargs):
    if not compiled_q:
        compiled_q = Q(**kwargs)

    if q_obj:
        return q_obj & compiled_q
    return compiled_q

def _compile_and_not(q_obj=None, compiled_q=None, **kwargs):
    if not compiled_q:
        compiled_q = Q(**kwargs)

    if q_obj:
        return q_obj & ~compiled_q
    return compiled_q

def _compile_or(q_obj=None, compiled_q=None, **kwargs):
    if not compiled_q:
        compiled_q = Q(**kwargs)

    if q_obj:
        return q_obj | compiled_q
    return compiled_q

def _compile_or_not(q_obj=None, compiled_q=None, **kwargs):
    if not compiled_q:
        compiled_q = ~Q(**kwargs)

    if q_obj:
        return q_obj | compiled_q
    return compiled_q

def _compile_xor(q_obj=None, compiled_q=None, **kwargs):
    if not compiled_q:
        arg1, arg2 = kwargs.items()
        arg1, arg2 = {arg1[0]: arg1[1]}, {arg2[0]: arg2[1]}
        compiled_q = (Q(**arg1) and ~Q(**arg2)) | (Q(**arg2) and ~Q(**arg1))

    if q_obj:
        return q_obj & compiled_q

    return compiled_q

def _compile_args(operation_kwargs, **kwargs):
    compiled_kwargs = {key: value if not callable(value) else value(**kwargs) for key, value in operation_kwargs.items()}
    return compiled_kwargs

class QueryBuilder:
    @staticmethod
    def where(**kwargs):
        return QueryBuilder().and_where(**kwargs)
    
    @staticmethod
    def where_not(**kwargs):
        return QueryBuilder().and_not_where(**kwargs)

    def __init__(self):
        self._query = []
        self._cached_q = None

    def _add_operation(self, operation, **kwargs):
        if not any(callable(value) for value in kwargs.values()):
            self._query.append({
                'operation': operation,
                'cached': operation(**kwargs)
            })
            return

        ignore_no_args_eval = kwargs.pop('ignore_no_args_eval', False)
        self._query.append({
            'operand': operation,
            'ignore_none_args': ignore_no_args_eval,
            'kwargs': kwargs
        })
     
    def and_where(self, **kwargs):
        self._add_operation(_compile_and, **kwargs)
        return self

    def and_not_where(self, **kwargs):
        self._add_operation(_compile_and_not, **kwargs)
        return self
        
    def or_where(self, **kwargs):
        self._add_operation(_compile_or, **kwargs)
        return self
    
    def or_not_where(self, **kwargs):
        self._add_operation(_compile_or_not, **kwargs)
        return self
    
    def where_one_not_both(self, **kwargs):
        if len(kwargs) != 2:
            raise Exception('XOR requires ONLY a left and right operand (2 keyword arguments required)')
        self._add_operation(_compile_xor, **kwargs)
        return self
    
    def build(self, do_cache=False, ignore_cache=False, **kwargs):
        if self._cached_q and not ignore_cache:
            return self._cached_q

        should_cache = True
        q_obj = None

        for operation in self._query:
            operation_func = operation['operation']
            compiled_q = operation.get('cached')

            if not compiled_q:
                should_cache = False
                op_kwargs = _compile_args(**kwargs)
                if len(op_kwargs) == 0 and operation['ignore_none_args']:
                    continue
                q_obj = operation_func(q_obj=q_obj, **op_kwargs)
            else:
                q_obj = operation_func(q_obj=q_obj, compiled_q=compiled_q)
        
        if should_cache or do_cache:
            self._cached_q = q_obj

        return q_obj
    
    def filter_against(self, queryset, **kwargs):
        q_obj = self.build(**kwargs)
        return queryset.filter(q_obj)
    
    def to_check(self):
        return QueryBuilderCheck(self)

class filter_keyword_args:
    def __init__(self):
        self._function_signature = None
    
    def _parse_args(self, *args, **kwargs):
        if self.accepts_var_args:
            required_args = args[0:self.required_args]
            var_args = args[self.required_args:]
        else:
            args_passed = len(args)
            if args_passed != self.required_args:
                raise Exception(f'Method requires exactly {self.required_args} arguments ({args_passed} arguments were used)')
            required_args = args
            var_args = []

        missing_kwargs = []
        for keyword in self.required_keywords:
            if keyword not in kwargs:
                missing_kwargs.append(keyword)
        
        if missing_kwargs:
            raise Exception(f'Method requires the keywords {", ".join(self.required_keywords)} arguments ({", ".join(missing_kwargs)} are missing)')

        if self.accepts_var_kwargs:
            accepted_kwargs = kwargs
        else:
            accepted_kwargs = {key: kwargs[key] for key in self.required_keywords}

        return required_args, var_args, accepted_kwargs

    def __call__(self, func):
        self._function_signature = inspect.signature(func)

        @wraps(func)
        def wrapped_function(*args, **kwargs):
            if any(param.kind == param.VAR_KEYWORD for param in self._function_signature.parameters.values()):
                bound_args = self._function_signature.bind(*args, **kwargs)
                bound_args.apply_defaults()
                return func(**bound_args.arguments)
            else:
                kwargs = {
                    param_name: kwargs[param_name]
                    for param_name, param in self._function_signature.parameters.items() if (
                        param.kind is param.KEYWORD_ONLY or
                        param.kind is param.POSITIONAL_OR_KEYWORD
                    ) and
                    param_name in kwargs
                }
                return func(*args, **kwargs)
        return wrapped_function