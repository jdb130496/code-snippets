// Compilation (With Powershell alias): 
// clang-win -std=c++20 -fsyntax-only -xc++ repro_GH198663.cpp; echo "Exit code: $LASTEXITCODE" for 22.1.8 in Windows,
// Followed by use-gcc alias and then,
//g++ -std=c++20 -fsyntax-only -xc++ repro_GH198663.cpp; echo "Exit code: $LASTEXITCODE"
// For msys clang 22.1.7
// repro_GH198663.cpp
//
// Reproducer for https://github.com/llvm/llvm-project/issues/198663
// Fixed by PR #199617, cherry-picked into the 22.1.8 patch release.
// Bug: Clang 22.1.7 (and earlier) incorrectly hashed the constraint
// ("requires" clause) of a member function template when that
// constraint depended on a type reached through an inherited
// `using` declaration. Two constraints that are NOT equivalent
// were sometimes hashed identically, so overload resolution /
// constraint checking gave the wrong answer.
//
// This is a pure frontend (Sema) bug -- no codegen, no ABI, no
// standard library involved. It should reproduce identically on
// any target (MSVC or GNU), which is what makes it a clean,
// apples-to-apples test of the 22.1.7 -> 22.1.8 patch itself,
// independent of clang-win vs clang-msys being different toolchains.
//
// Expected result:
//   clang 22.1.7 (buggy):  static_assert(!CanAt<NonTransparentMap>) FAILS
//                           -> compile error pointing at that line
//   clang 22.1.8 (fixed):  compiles cleanly, no diagnostics

template <class T>
concept HasIsTransparent = requires { typename T::is_transparent; };

template <class K, class V, class Compare>
struct FlatMapBase {
    using key_compare = Compare;
};

template <class K, class V, class Compare>
struct FlatMap : FlatMapBase<K, V, Compare> {
    using Base = FlatMapBase<K, V, Compare>;

    using typename Base::key_compare;

    void at(const K&) {}
    void at(const K&) const {}
    template <class Other>
    void at(const Other&)
        requires HasIsTransparent<key_compare>
    {}
    template <class Other>
    void at(const Other&) const
        requires HasIsTransparent<key_compare>
    {}
};

template <class T>
struct Transparent {
    T t;
};

struct TransparentComparator {
    using is_transparent = void;

    template <class T>
    bool operator()(const T&, const Transparent<T>&) const;

    template <class T>
    bool operator()(const Transparent<T>&, const T& t) const;

    template <class T>
    bool operator()(const T&, const T&) const;
};

struct NonTransparentComparator {
    template <class T>
    bool operator()(const T&, const Transparent<T>&) const;

    template <class T>
    bool operator()(const Transparent<T>&, const T&) const;

    template <class T>
    bool operator()(const T&, const T&) const;
};

template <class M>
concept CanAt = requires(M m, Transparent<int> k) { m.at(k); };

using TransparentMap = FlatMap<int, double, TransparentComparator>;
using NonTransparentMap = FlatMap<int, double, NonTransparentComparator>;

// This one passes on both versions -- not the interesting line.
static_assert(CanAt<TransparentMap>);

// THIS is the line that distinguishes the two compiler versions.
// It must hold (NonTransparentComparator has no is_transparent,
// so .at(Transparent<int>) must NOT be callable). Clang 22.1.7's
// hashing bug makes it wrongly think this constraint is satisfied,
// so the static_assert fails to compile under 22.1.7 and succeeds
// (silently, no output) under 22.1.8.
static_assert(!CanAt<NonTransparentMap>);

int main() { return 0; }
