from .optimizer import Optimizer
from ..optimizer_result import OptimizerResult
from numpy.random import uniform
from numpy.linalg import norm
import numpy as np

# TODO №1 Добавить в вывод в результат безразмерных параметров
# TODO №2 Добавить сохранение истории поиска
# TODO №3 Подумать над рандомизированной фиксацией некоторых компонент вектора варьируемых параметров

class RandomOptimizer(Optimizer):

    def __init__(self, dropout=False, dropout_proba=0.5):

        self._dropout = dropout
        self._dropout_proba = dropout_proba


class RandomSearchOptimizer(RandomOptimizer):

    def __init__(self, N=100, M=10, t0=1., R=0.1, alpha=1.618, beta=0.618,
                 min_delta_f=0., random_state=42, dropout=False, dropout_proba=0.5):

        super().__init__(dropout=dropout, dropout_proba=dropout_proba)
        self.N = N
        self.M = M
        self.t0 = t0
        self.R = R
        self.alpha = alpha
        self.beta = beta
        self.min_delta_f = min_delta_f

        np.random.seed(random_state)

    def show_options(self):
        print(
            f'N = {self.N}',
            f'M = {self.M}',
            f't0 = {self.t0}',
            f'R = {self.R}',
            f'alpha = {self.alpha}',
            f'beta = {self.beta}',
            f'min_delta_f = {self.min_delta_f}',
            sep='\n'
        )

    def _get_yj(self, x_cur, tk):
        """

        :param x_cur:
        :param tk:
        :return:
        """
        ksi = uniform(-1, 1, len(x_cur))

        if self._dropout:
            dropout_mask = np.random.rand(x_cur.shape[0]) > self._dropout_proba
        else:
            dropout_mask = np.ones(x_cur.shape[0])

        yj = x_cur + dropout_mask * tk * ksi / norm(ksi)
        return yj

    def _get_zj(self, x_cur, alpha, yj):
        """

        :param x_cur:
        :param alpha:
        :param yj:
        :return:
        """
        zj = x_cur + alpha * (yj - x_cur)
        return zj

    def optimize(self,
                 t_func,
                 x0,
                 args=tuple(),
                 bounds=None,
                 constraints=None,
                 out_func=None):

        f_evals = 0
        f_evals_errs = 0
        steps_total = 0
        bad_steps_cur = 1

        search_history_x = []
        search_history_f = []

        try:
            last_x = np.ones_like(x0)
            bound_check = self._check_bounds(last_x*x0, bounds)
            constraints_check = self._check_constraints(last_x * x0, constraints, args)
            if not all((bound_check, constraints_check)):
                last_f = np.inf
            else:
                last_f = t_func(last_x * x0, *args)
                search_history_x.append((last_x * x0).copy())
                search_history_f.append(last_f)
                f_evals += 1

        except Exception as e:
            print('Ошибка на первом шаге')
            print(e)
            last_f = np.inf
            f_evals_errs += 1

        tk = self.t0

        while steps_total < self.N:
            while bad_steps_cur < self.M:

                yj = x0 * self._get_yj(last_x, tk)

                try:
                    bounds_check = self._check_bounds(yj, bounds)
                    constraints_check = self._check_constraints(yj, constraints, args)
                    if all((bounds_check, constraints_check)):
                        cur_f = t_func(yj, *args)
                        f_evals += 1
                        if (cur_f <= last_f) & (abs(cur_f - last_f) > self.min_delta_f):
                            zj = x0 * self._get_zj(last_x, self.alpha, yj/x0)
                            bounds_check = self._check_bounds(zj, bounds)
                            constraints_check = self._check_constraints(zj, constraints, args)
                            if all((bounds_check, constraints_check)):
                                cur_f = t_func(zj, *args)
                                f_evals += 1
                                if (cur_f <= last_f) & (abs(cur_f - last_f) > self.min_delta_f):
                                    last_x, last_f = zj / x0, cur_f

                                    search_history_x.append(zj.copy())
                                    search_history_f.append(last_f)

                                    tk *= self.alpha
                                    steps_total += 1
                                    if out_func:
                                        out_func(last_f, zj, *args)
                                    break
                                else:
                                    bad_steps_cur += 1
                            else:
                                bad_steps_cur += 1
                        else:
                            bad_steps_cur += 1
                    else:
                        bad_steps_cur += 1
                except:
                    bad_steps_cur += 1
                    f_evals += 1
                    f_evals_errs += 1

            if tk <= self.R:

                if np.array_equal(last_x, np.ones_like(last_x)):
                    return OptimizerResult(
                        last_x*x0,
                        last_f,
                        f_evals=f_evals,
                        f_eval_errs=f_evals_errs,
                        status=False,
                        status_message='Оптимизация завершилась неудачно, достигнут минимальный шаг.',
                        f_history=np.array(search_history_f),
                        x_history=np.array(search_history_x),
                        bounds=bounds,
                        constraints=constraints
                    )
                else:
                    return OptimizerResult(
                        last_x * x0,
                        last_f,
                        f_evals=f_evals,
                        f_eval_errs=f_evals_errs,
                        status=True,
                        status_message='Оптимизация завершилась удачно, достигнут минимальный шаг.',
                        f_history=np.array(search_history_f),
                        x_history=np.array(search_history_x),
                        bounds=bounds,
                        constraints=constraints
                    )
            else:
                tk *= self.beta
                bad_steps_cur = 1

        return OptimizerResult(
            last_x * x0,
            last_f,
            f_evals=f_evals,
            f_eval_errs=f_evals_errs,
            status=False,
            status_message='Оптимизация завершилась неудачно, исчерпан лимит удачных шагов.',
            f_history=np.array(search_history_f),
            x_history=np.array(search_history_x),
            bounds=bounds,
            constraints=constraints
        )

class SRandomSearchOptimizer(RandomOptimizer):

    def __init__(self, N=50, min_delta_f=0., random_state=42, dropout=False, dropout_proba=0.5):

        super().__init__(dropout=dropout, dropout_proba=dropout_proba)
        self.N = N
        self.min_delta_f = min_delta_f

        np.random.seed(random_state)

    def show_options(self):
        print(
            f'N = {self.N}',
            f'min_delta_f = {self.min_delta_f}',
            sep='\n'
        )

    def get_delta_z(self, K, max_bad_steps_cur, bad_steps_cur):
        '''
        Расчет приращения
        '''

        if self._dropout:
            dropout_mask = np.random.rand(K) > self._dropout_proba
        else:
            dropout_mask = np.ones(K)

        H = np.random.randn(K)
        m = (1./(10*np.sqrt(K))) * np.exp(-1e-3*(bad_steps_cur**2/self.N**2 + max_bad_steps_cur**2/self.N**2))
        return m*H*dropout_mask

    def optimize(self,
                 t_func,
                 x0_vec,
                 bounds,  # Границы поиска (ограничения 1 рода)
                 args=tuple(),
                 constraints=None,
                 out_func=None):

        f_evals = 0
        f_evals_errs = 0
        max_bad_steps_cur = 0  # Максимальное число неудачных шагов среди всех опорных точек
        bad_steps_cur = 0  # Число неудачных шагов из одной опорной точки

        search_history_x = []
        search_history_f = []

        K = len(x0_vec)
        z = np.ones(K) * 0.5
        last_z = np.ones(K) * 0.5
        lims = np.array([bound.to_list() for bound in bounds])

        xx = x0_vec.copy()
        last_xx = x0_vec.copy()

        try:
            constraints_check = self._check_constraints(last_xx, constraints, args)
            if not constraints_check:
                last_f = np.inf
            else:
                last_f = t_func(last_xx, *args)
                search_history_x.append(last_xx.copy())
                search_history_f.append(last_f)
                f_evals += 1

        except Exception as e:
            print('Ошибка на первом шаге')
            print(e)
            last_f = np.inf

        while bad_steps_cur <= self.N:
            try:
                dz = self.get_delta_z(K, max_bad_steps_cur, bad_steps_cur)
                z += dz

                for k in range(K):
                    if z[k] > 1.:
                        z[k] = 1.
                    if z[k] < 0.:
                        z[k] = 0.

                xx = lims[:, 0] + (lims[:, 1] - lims[:, 0])*z
                constraints_check = self._check_constraints(xx, constraints, args)
                if constraints_check:
                    cur_f = t_func(xx, *args)
                    f_evals += 1
                    if (cur_f <= last_f) & (abs(cur_f - last_f) > self.min_delta_f):
                        last_f, last_z, last_xx = cur_f, z.copy(), xx.copy()

                        search_history_x.append(last_xx.copy())
                        search_history_f.append(last_f)

                        max_bad_steps_cur = max(max_bad_steps_cur, bad_steps_cur)
                        bad_steps_cur = 0

                        if out_func:
                            out_func(last_f, last_xx, *args)

                    else:
                        bad_steps_cur += 1
                else:
                    bad_steps_cur += 1
            except:
                f_evals_errs += 1
                bad_steps_cur += 1

        if np.array_equal(last_z, np.ones(K)*0.5):
            return OptimizerResult(
                last_xx,
                last_f,
                f_evals=f_evals,
                f_eval_errs=f_evals_errs,
                status=False,
                status_message='Оптимизация завершилась неудачно, израсходованно макс. число неудачных шагов.',
                f_history=np.array(search_history_f),
                x_history=np.array(search_history_x),
                bounds=bounds,
                constraints=constraints
            )
        return OptimizerResult(
            last_xx,
            last_f,
            f_evals=f_evals,
            f_eval_errs=f_evals_errs,
            status=True,
            status_message='Оптимизация завершилась удачно, израсходованно макс. число неудачных шагов.',
            f_history=np.array(search_history_f),
            x_history=np.array(search_history_x),
            bounds=bounds,
            constraints=constraints
        )








