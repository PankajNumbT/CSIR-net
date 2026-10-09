"""Finish six previously pending questions without touching existing packs."""
from pack_writer import Writer

w = Writer('2024-june', '-q113')
w.add(113, 'Statistics', 'Statistical Inference', 'Hard',
r'''Let independent $Y_i\sim N(\beta x_i,\sigma^2)$, $n\ge2$, where the $x_i$ and $\sigma^2>0$ are known. Give $\beta$ the prior $N(\beta_0,\tau^2)$, $\tau^2>0$. Under squared error loss, which statements about the Bayes estimate are true? The printed question does not require $\sum x_i^2>0$.''',
[r'It tends to $\beta_0$ as $\tau^2\to0$.', r'It tends to $\bar y/\bar x$ as $\tau^2\to0$.', r'It tends to the BLUE as $\tau^2\to\infty$.', r'It tends to the MLE as $\tau^2\to\infty$.'], 'ACD',
[r'Complete the square in the product of the normal likelihood and prior.', r'Check both $S=\sum x_i^2>0$ and the allowed degenerate case $S=0$.'],
r'''Set $S=\sum x_i^2$ and $T=\sum x_iY_i$. Completing the square gives posterior variance $v=(\tau^{-2}+S/\sigma^2)^{-1}$ and posterior mean
$$m=\frac{\sigma^2\beta_0+\tau^2T}{\sigma^2+\tau^2S}.$$
The mean minimizes posterior squared error. As $\tau^2\to0$, $m\to\beta_0$: A holds and B is not a general conclusion (even $\bar x=0$ is allowed). If $S>0$, $m\to T/S$ as $\tau^2\to\infty$. This is both the BLUE and the unique MLE, giving the **intended A,C,D**, also the official key for question ID 704113.

The source omits the nonzero-design hypothesis. If all $x_i=0$, the data distribution does not depend on $\beta$, $m=\beta_0$ at every prior variance, no unbiased estimator of $\beta$ exists, and every real value maximizes the likelihood. Thus the BLUE and unique-MLE limits in C,D are not defined in that case. **This item is unscored as printed; A,C,D apply to the identifiable model $S>0$.**''',
r'''Normal conjugacy adds information through precisions: the prior contributes $\tau^{-2}$ and the likelihood contributes $S/\sigma^2$. Squared error loss leads to the posterior mean because conditional risk equals the posterior variance plus the squared distance from that mean. A concentrated prior dominates as its variance tends to zero. A diffuse prior yields the least-squares estimate only when the design identifies the parameter. In regression through the origin, identification requires $S>0$, and the relevant statistic is $T=\sum x_iY_i$, not the ratio of sample means. Cauchy–Schwarz proves the BLUE property: a linear unbiased estimator has coefficients with $a^\top x=1$ and variance $\sigma^2\|a\|^2\ge\sigma^2/S$, attained at $a=x/S$. Differentiating the normal log likelihood yields the same estimate. When $S=0$, observations contain no information about the parameter and these inference claims require separate treatment.''',
[(r'For $x=(1,2)$, $Y=(2,5)$, $\sigma^2=1$, prior mean $0$ and variance $t$, find the Bayes estimate.', r'$S=5,T=12$, so $m=12t/(1+5t)$. It tends to $0$ as $t\to0$ and $12/5$ as $t\to\infty$, the OLS/MLE.'),
 (r'If all design entries are zero, how does a $N(3,7)$ prior change after observing the sample?', r'The likelihood is constant in $\beta$, so the posterior remains $N(3,7)$ and the squared-error Bayes estimate stays $3$. Any statistic has the same expectation for every $\beta$, so none can be unbiased for $\beta$.')],
status='source_issue', note='Original attached question lacks the nonzero-design condition; intended A,C,D agrees with NTA final key, ID 704113, page 3: https://nta.ac.in/Download/Notice/Notice_20240911185103.pdf')

w = Writer('2025-december', '-q116-120')
w.add(116, 'Mathematics', 'Integral Equations', 'Moderate',
r'''A nontrivial solution of $y(x)=\lambda\int_{-1}^{1}(5xt^3+4x^2t+3xt)y(t)\,dt$ satisfies $y(1)=5/2$. Which statements are true?''',
[r'$y(0)+y^\prime(0)=3/2$', r'$y(1/2)+y^\prime(1/2)=7/2$', r'$y(-1)+y^\prime(-1)=-1$', r'$y(1/3)+y^\prime(1/3)=14/9$'], 'ABC',
[r'The range of this integral operator lies in the span of $x$ and $x^2$.', r'Put $y=ax+bx^2$ and use the vanishing of odd integrals over $[-1,1]$.'],
r'''The right side is a polynomial of the form $ax+bx^2$, so every solution has that form. Symmetry gives $\int_{-1}^1ty(t)\,dt=2a/3$ and $\int_{-1}^1t^3y(t)\,dt=2a/5$. Consequently
$$ax+bx^2=\lambda\left(4ax+\frac{8a}{3}x^2\right).$$
If $a=0$, the equations force $b=0$, contrary to nontriviality. Hence $\lambda=1/4$ and $b=2a/3$. The condition $a+b=5/2$ yields $a=3/2,b=1$. Therefore $y=x^2+3x/2$, and
$$y(x)+y^\prime(x)=x^2+\frac72x+\frac32.$$
Its values at $0,1/2,-1,1/3$ are respectively $3/2,7/2,-1,25/9$. **A,B,C are correct; D is false.**''',
r'''A degenerate, or finite-rank, kernel is a finite sum $K(x,t)=\sum_{j=1}^r a_j(x)b_j(t)$. Its integral operator has range in the span of the functions $a_j$, so a nonzero solution of a homogeneous equation $y=\lambda Ty$ must lie in that finite-dimensional space. Substitution reduces the integral equation to a matrix eigenvalue problem. The nonzero eigenvalues of $T$ correspond to the characteristic values $\lambda$ through reciprocals. Symmetry of the integration interval eliminates integrands that are odd, often making the coefficient equations triangular. The homogeneous equation initially determines an eigenfunction only up to scale; a normalization such as $y(1)=5/2$ fixes that scale when evaluation there is nonzero. It is essential to rule out the zero coefficient case before dividing and to substitute the resulting polynomial back into the original equation.''',
[(r'Solve $y(x)=\lambda x\int_{-1}^1ty(t)\,dt$ nontrivially, with $y(1)=2$.', r'Write $y=ax$. The integral is $2a/3$, so $a=\lambda(2a/3)$ gives $\lambda=3/2$. Normalization gives $a=2$, hence $y=2x$.'),
 (r'For $Ty=x\int_{-1}^1ty(t)\,dt+x^2\int_{-1}^1t^2y(t)\,dt$, find the eigenvalues on its range.', r'For $y=ax+bx^2$, symmetry gives $Ty=(2a/3)x+(2b/5)x^2$. The eigenvalues are $2/3,2/5$, with eigenfunctions $x,x^2$; $y=\lambda Ty$ has characteristic values $3/2,5/2$.')])

w.add(117, 'Mathematics', 'Numerical Analysis', 'Moderate',
r'''Newton–Raphson iteration for $\sin x-1=0$ converges to $\alpha=\pi/2$. Put $e_n=x_n-\alpha$. For which $p>0$ does $\lim |e_{n+1}|/|e_n|^p$ exist as a finite nonzero constant, and what is that constant? Assume errors are nonzero along the asymptotic sequence.''',
[r'$p=1$', r'The limit is $1/2$.', r'$p=2$', r'The limit is $1$.'], 'AB',
[r'At $\pi/2$, both the function and its first derivative vanish.', r'Use $\sin(\pi/2+e)=\cos e$ and the half-angle identity for $(1-\cos e)/\sin e$.'],
r'''Newton's update is $x_{n+1}=x_n-(\sin x_n-1)/\cos x_n$. In error coordinates,
$$e_{n+1}=e_n-\frac{1-\cos e_n}{\sin e_n}
=e_n-\tan(e_n/2)
=\frac{e_n}{2}-\frac{e_n^3}{24}+O(e_n^5).$$
Thus $|e_{n+1}|/|e_n|\to1/2$. More generally, the ratio with power $p$ behaves as $\tfrac12|e_n|^{1-p}$: its limit is zero if $p<1$, finite nonzero only if $p=1$, and unbounded if $p>1$. **A,B are correct.** The root has multiplicity two, so the usual simple-root quadratic convergence theorem does not apply.''',
r'''The order of convergence is measured through the asymptotic error relation $|e_{n+1}|\sim C|e_n|^p$, with $0<C<\infty$. Newton's method has order two near a simple root when the needed smoothness and nonzero derivative assumptions hold. If $f(x)=(x-\alpha)^m g(x)$ with $g(\alpha)\ne0$ and multiplicity $m>1$, expansion instead gives $e_{n+1}=(1-1/m)e_n+O(e_n^2)$, hence linear convergence with factor $(m-1)/m$. For $\sin x-1$, the Taylor expansion about $\pi/2$ starts at $-e^2/2$, identifying a double root. Exact trigonometric identities simplify the update and reveal the next error term. Modified Newton iteration subtracting $m f/f'$ removes the linear term when the multiplicity is known; its order can be higher in special symmetric examples. Derivative vanishing at the root also means the direct quotient must be evaluated at nearby nonroot iterates.''',
[(r'Apply ordinary Newton iteration to $(x-a)^2=0$. What happens to the error?', r'For $e\ne0$, $f/f^\prime=e/2$, so the next error is exactly $e/2$. The convergence is linear with factor $1/2$.'),
 (r'For Newton iteration on $x^2-2=0$ near $\sqrt2$, derive the error relation.', r'$x_{n+1}=(x_n+2/x_n)/2$. Subtracting $\sqrt2$ gives $e_{n+1}=e_n^2/(2x_n)$, so the order is two and constant $1/(2\sqrt2)$.')])

w.add(118, 'Mathematics', 'Partial Differential Equations', 'Moderate',
r'''Consider the Dirichlet problem $u_{xx}+u_{yy}=0$ inside the unit disk with continuous boundary data $u(x,y)=e^{x+y}$ on $x^2+y^2=1$. Which statements are true for the classical solution continuous on the closed disk?''',
[r'A unique solution exists.', r'No solution exists.', r'$u=(1+e)/2$ at some point of the closed disk.', r'$u=(1+e^3)/2$ at some point of the closed disk.'], 'AC',
[r'Continuous boundary data on a disk admit a harmonic Poisson extension.', r'On the circle, $-\sqrt2\le x+y\le\sqrt2$; use the maximum principle.'],
r'''Continuous boundary data have a Poisson integral extension that is harmonic inside and continuous up to the circle. The maximum principle gives uniqueness and
$$e^{-\sqrt2}\le u(x,y)\le e^{\sqrt2}.$$
Thus A is true and B false. The number $(1+e)/2$ lies strictly between $1$ and $e$, hence within the boundary range $[e^{-\sqrt2},e^{\sqrt2}]$. Since $x+y$ runs continuously through $[-\sqrt2,\sqrt2]$ on the circle, the boundary already attains this value. C is true.

For D, $(1+e^3)/2>e^3/2>e^{\sqrt2}$: the last inequality follows from $e^{3-\sqrt2}>e>2$. It violates the upper bound, so D is false. **A,C are correct.** The interior solution is not simply $e^{x+y}$, whose Laplacian is $2e^{x+y}$.''',
r'''For a continuous function $g$ on the boundary of the unit disk, the Poisson formula is $u(r,\theta)=\frac1{2\pi}\int_0^{2\pi}\frac{1-r^2}{1-2r\cos(\theta-t)+r^2}g(t)\,dt$. It produces a harmonic function for $r<1$ with the prescribed continuous boundary limits. The kernel is nonnegative and has integral one, so the extension stays between the boundary minimum and maximum. Alternatively, the maximum principle gives these bounds and proves uniqueness by applying it to the difference of two solutions. To decide whether a value occurs somewhere on the closed disk, it is often enough to check the continuous boundary range. Boundary data need not be harmonic as a formula on the interior; the extension problem prescribes only their values on the circle. Continuity and the stated solution class matter for both existence and uniqueness.''',
[(r'Find the harmonic extension of boundary data $g(\theta)=2+\cos(3\theta)$ on the unit circle.', r'$u(r,\theta)=2+r^3\cos(3\theta)$. Each polar mode is harmonic, and at $r=1$ it gives the required values. Uniqueness follows from the maximum principle.'),
 (r'If continuous boundary data lie in $[4,7]$, can the continuous harmonic extension attain $9$ inside?', r'No. The maximum principle bounds the extension above by $7$ and below by $4$. If it attains either global extreme at an interior point, the strong maximum principle makes it constant.')])

w.add(119, 'Statistics', 'Regression and Multivariate Analysis', 'Hard',
r'''In $Y_i=\beta x_i+\varepsilon_i$, let $\beta>0$, $S=\sum x_i^2>0$, and uncorrelated errors have mean zero and variance $\sigma^2>0$. Let $\widetilde\beta_1=\sum a_i^*Y_i$, where the coefficients minimize $E(\sum a_iY_i-\beta)^2$ over all real coefficients, and let $\widetilde\beta_2$ be OLS. Which comparison is true?''',
[r'$\operatorname{Var}(\widetilde\beta_1)>\operatorname{Var}(\widetilde\beta_2)$ and $\operatorname{MSE}(\widetilde\beta_1)>\operatorname{MSE}(\widetilde\beta_2)$.',
 r'$\operatorname{Var}(\widetilde\beta_1)<\operatorname{Var}(\widetilde\beta_2)$ and $\operatorname{MSE}(\widetilde\beta_1)<\operatorname{MSE}(\widetilde\beta_2)$.',
 r'$\operatorname{Var}(\widetilde\beta_1)>\operatorname{Var}(\widetilde\beta_2)$ and $E\widetilde\beta_1<E\widetilde\beta_2$.',
 r'$\operatorname{Var}(\widetilde\beta_1)<\operatorname{Var}(\widetilde\beta_2)$ and $E\widetilde\beta_1>E\widetilde\beta_2$.'], 'B',
[r'Write risk as $\sigma^2\|a\|^2+\beta^2(a^\top x-1)^2$.', r'The unrestricted optimum shrinks the unbiased OLS estimator toward zero.'],
r'''The risk is $\sigma^2a^\top a+\beta^2(a^\top x-1)^2$. Its strictly positive definite Hessian gives a unique minimum satisfying
$$(\sigma^2I+\beta^2xx^\top)a^*=\beta^2x,\qquad a^*=\frac{\beta^2x}{\sigma^2+\beta^2S}.$$
OLS is $\widetilde\beta_2=x^\top Y/S$. Therefore $\widetilde\beta_1=c\widetilde\beta_2$, where $c=\beta^2S/(\sigma^2+\beta^2S)\in(0,1)$. We have
$$E\widetilde\beta_1=c\beta<\beta,\quad
\operatorname{Var}(\widetilde\beta_1)=c^2\frac{\sigma^2}{S}<\frac{\sigma^2}{S},$$
and the minimum MSE is $\beta^2\sigma^2/(\sigma^2+\beta^2S)=c\sigma^2/S<\sigma^2/S$, the OLS MSE. **B is correct.** The optimum depends on unknown $\beta$; it is a pointwise oracle comparison, not an implementable estimator claimed to improve uniformly.''',
r'''For any estimator, mean squared error equals variance plus squared bias. A linear estimator $a^\top Y$ in this regression has expectation $\beta a^\top x$ and variance $\sigma^2\|a\|^2$ because errors are uncorrelated with common variance. Gauss–Markov minimizes variance subject to the unbiasedness constraint $a^\top x=1$, yielding OLS coefficients $x/S$. Removing that constraint permits shrinkage: reduced variance can outweigh the induced bias for a specified parameter value. The optimal factor here balances the terms $c^2\sigma^2/S$ and $(1-c)^2\beta^2$. Its dependence on the unknown parameter is crucial: pointwise minimum risk over coefficients is an oracle calculation, not evidence that a fixed practical coefficient vector dominates OLS for every $\beta$. Positive error variance and nonzero design make the optimum strict and ensure all denominators are positive.''',
[(r'If $\beta=2$, $S=3$, and $\sigma^2=4$, compare the oracle estimator with OLS.', r'$c=12/(4+12)=3/4$. OLS has variance and MSE $4/3$. The oracle has mean $3/2$, variance $(9/16)(4/3)=3/4$, squared bias $1/4$, and MSE $1$.'),
 (r'An unbiased estimator has variance $v$. Find the pointwise MSE-optimal constant multiplier when estimating a parameter $\theta$.', r'Risk of $cT$ is $c^2v+(1-c)^2\theta^2$. Differentiating gives $c=\theta^2/(v+\theta^2)$ and minimum risk $v\theta^2/(v+\theta^2)$. Since $c$ depends on $\theta$, this is an oracle factor.')])

w.add(120, 'Mathematics', 'Complex Analysis', 'Hard',
r'''Let $f:\mathbb C\to\mathbb C$ be $f(z)=\sin^2z+\cos^2|z|$. Which statements are true?''',
[r'$f$ is real valued.', r'$f(z)=1$ for every $z$.', r'$f$ is not entire.', r'$f$ has finitely many zeros on the imaginary axis.'], 'CD',
[r'The identity $\sin^2z+\cos^2z=1$ uses the same argument in both terms.', r'For $z=iy$, reduce to $\cos^2y-\sinh^2y$, an even real function.'],
r'''For $z=x+iy$, $\operatorname{Im}\sin^2z=\tfrac12\sin(2x)\sinh(2y)$, whereas $\cos^2|z|$ is real. Taking $x=\pi/4,y=1$ disproves A. At $z=i$, $f(i)=\cos^2(1)-\sinh^2(1)<0$, disproving B since $f(0)=1$.

If $f$ were entire, subtracting the entire function $\sin^2z$ would make $h(z)=\cos^2|z|$ an entire real-valued function. Such a function is constant by the Cauchy–Riemann equations; yet $h(0)=1$ and $h(\pi/2)=0$. Thus C holds.

On the imaginary axis, $F(y)=f(iy)=\cos^2y-\sinh^2y$. Put $a=\operatorname{arsinh}(1)<\pi/2$. For $|y|>a$, $F(y)<0$. On $(0,a)$, $F^\prime(y)=-\sin(2y)-\sinh(2y)<0$, while $F(0)=1$ and $F(a)=\cos^2a-1<0$. Hence there is exactly one positive zero and, by evenness, one negative zero. **Exactly two imaginary-axis zeros: C,D are correct.**''',
r'''Complex trigonometric identities remain valid for complex arguments, but replacing an argument with its modulus introduces dependence on both $z$ and its conjugate. A nonconstant real-valued function on a connected open subset of the plane cannot be holomorphic: the Cauchy–Riemann equations force both first partial derivatives of its real part to vanish. This provides a useful test after subtracting a known entire term. Nonholomorphic functions do not generally satisfy the isolated-zero theorem for holomorphic functions, so zeros should be studied directly. Restricting to the imaginary axis uses $\sin(iy)=i\sinh y$ and the fact that cosine squared is even. Growth of the hyperbolic term confines all zeros to a bounded interval; strict monotonicity on the positive part and symmetry then give an exact count. Boundedness alone would not establish finiteness for an arbitrary continuous function.''',
[(r'Is $g(z)=z+|z|^2$ entire?', r'If it were, $g(z)-z=|z|^2$ would be holomorphic and real valued on $\mathbb C$, hence constant. Its values at $0$ and $1$ differ, so it is not entire.'),
 (r'For $b>0$, count the real zeros of $H(y)=b-\sinh^2y$.', r'It is even, positive at zero, and strictly decreasing for $y>0$. Solving $\sinh^2y=b$ gives exactly $y=\pm\operatorname{arsinh}(\sqrt b)$.')])

print('Saved six independently derived learning packs.')
