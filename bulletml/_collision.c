#include "Python.h"

#define STR_AND_SIZE(s) s, sizeof(s) - 1
#define DOT(x1, y1, x2, y2) ((x1) * (x2) + (y1) * (y2))
#define NEARZERO(d) ((d) < 0.0001 && (d) > -0.0001)

static const char *s_pchModDoc = "Optimized collision detection functions.";

static PyObject *s_ppykX;
static PyObject *s_ppykY;
static PyObject *s_ppykPX;
static PyObject *s_ppykPY;
static PyObject *s_ppykRadius;

static const char s_achOverlapsDoc[] = (
    "Return true if two circles are overlapping.\n\n"
    "Usually, you\'ll want to use the \'collides\' method instead, but\n"
    "this one can be useful for just checking to see if the player has\n"
    "entered an area or hit a stationary oject.\n\n"
    "(This function is optimized.)\n\n");

static const char s_achCollidesDoc[] = (
    "Return true if the two moving circles collide.\n\n"
    "The circles should have the following attributes:\n\n"
    "    x, y - required, current position\n"
    "    px, py - not required, defaults to x, y, previous frame position\n"
    "    radius - not required, defaults to 0.5\n\n"
    "(This function is optimized.)\n\n");

static const char s_achCollidesAllDoc[] = (
    "Filter the second argument to those that collide with the first.\n\n"
    "This is equivalent to filter(lambda o: collides(a, o), others),\n"
    "but is much faster when the compiled extension is available (which\n"
    "it is currently).\n\n");

// Get the attributes from a Python moving circle object.
static int GetCircle(PyObject *ppy, double *pdX, double *pdY,
                     double *pdPX, double *pdPY, double *pdR)
{
    PyObject *ppyf;

    if (!ppy)
        return 0;

    ppyf = PyObject_GetAttr(ppy, s_ppykX);
    if (ppyf)
    {
        *pdX = PyFloat_AsDouble(ppyf);
        Py_DECREF(ppyf);
    }

    ppyf = PyObject_GetAttr(ppy, s_ppykY);
    if (ppyf)
    {
        *pdY = PyFloat_AsDouble(ppyf);
        Py_DECREF(ppyf);
    }

    // Catch X or Y or failure to convert, any one of the four cases
    // is equally fatal. We don't need to check after each one.
    if (PyErr_Occurred())
        return 0;

    ppyf = PyObject_GetAttr(ppy, s_ppykPX);
    if (ppyf)
    {
        *pdPX = PyFloat_AsDouble(ppyf);
        Py_DECREF(ppyf);
        if (PyErr_Occurred())
            return 0;
    }
    else
    {
        PyErr_Clear();
        *pdPX = *pdX;
    }

    ppyf = PyObject_GetAttr(ppy, s_ppykPY);
    if (ppyf)
    {
        *pdPY = PyFloat_AsDouble(ppyf);
        Py_DECREF(ppyf);
        if (PyErr_Occurred())
            return 0;
    }
    else
    {
        PyErr_Clear();
        *pdPY = *pdY;
    }

    ppyf = PyObject_GetAttr(ppy, s_ppykRadius);
    if (ppyf)
    {
        *pdR = PyFloat_AsDouble(ppyf);
        Py_DECREF(ppyf);
        if (PyErr_Occurred())
            return 0;
    }
    else
    {
        PyErr_Clear();
        *pdR = 0.5;
    }

    return 1;
}

static int Collides(double dXA, double dXB, double dYA, double dYB,
                    double dPXA, double dPXB, double dPYA, double dPYB,
                    double dRA, double dRB)
{
    // Translate B's position to be relative to A's start.
    double dDirX = dPXA + (dXB - dXA) - dPXB;
    double dDirY = dPYA + (dYB - dYA) - dPYB;
    // Now A doesn't move. Treat B as a point by summing the radii.
    double dR = dRA + dRB;
    // Now the problem is just circle/line collision.

    double dDiffX = dPXA - dPXB;
    double dDiffY = dPYA - dPYB;

    // B didn't move relative to A, so early-out by doing point/circle.
    if (NEARZERO(dDirX) && NEARZERO(dDirY))
        return dDiffX * dDiffX + dDiffY * dDiffY <= dR * dR;
    else
    {
        double dT = (DOT(dDiffX, dDiffY, dDirX, dDirY)
                     / DOT(dDirX, dDirY, dDirX, dDirY));
        double dDistX;
        double dDistY;
        if (dT < 0.0) dT = 0.0;
        else if (dT > 1.0) dT = 1.0;

        dDistX = dPXA - (dPXB + dDirX * dT);
        dDistY = dPYA - (dPYB + dDirY * dT);

        return dDistX * dDistX + dDistY * dDistY <= dR * dR;
    }
}

static PyObject *py_overlaps(PyObject *ppySelf, PyObject *ppyArgs) {
    double dXA, dYA, dPXA, dPYA, dRA;
    double dXB, dYB, dPXB, dPYB, dRB;
    PyObject *ppyA, *ppyB;
    if (PyArg_ParseTuple(ppyArgs, "OO", &ppyA, &ppyB)
        && GetCircle(ppyA, &dXA, &dYA, &dPXA, &dPYA, &dRA)
        && GetCircle(ppyB, &dXB, &dYB, &dPXB, &dPYB, &dRB))
    {
        double dX = dXA - dXB;
        double dY = dYA - dYB;
        double dR = dRA + dRB;

        if (dX * dX + dY * dY <= dR * dR)
        {
            Py_RETURN_TRUE;
        }
        else
        {
            Py_RETURN_FALSE;
        }
    }
    else
        return NULL;
}

static PyObject *py_collides(PyObject *ppySelf, PyObject *ppyArgs)
{
    double dXA, dYA, dPXA, dPYA, dRA;
    double dXB, dYB, dPXB, dPYB, dRB;
    PyObject *ppyA, *ppyB;
    if (PyArg_ParseTuple(ppyArgs, "OO", &ppyA, &ppyB)
        && GetCircle(ppyA, &dXA, &dYA, &dPXA, &dPYA, &dRA)
        && GetCircle(ppyB, &dXB, &dYB, &dPXB, &dPYB, &dRB))
    {
        if (Collides(dXA, dXB, dYA, dYB, dPXA, dPXB, dPYA, dPYB, dRA, dRB))
        {
            Py_RETURN_TRUE;
        }
        else
        {
            Py_RETURN_FALSE;
        }
    }
    else
        return NULL;
}

static PyObject *py_collides_all(PyObject *ppySelf, PyObject *ppyArgs)
{
    double dXA, dYA, dPXA, dPYA, dRA;
    PyObject *ppyA, *ppyOthers;
    if (PyArg_ParseTuple(ppyArgs, "OO", &ppyA, &ppyOthers)
        && GetCircle(ppyA, &dXA, &dYA, &dPXA, &dPYA, &dRA))
    {
        PyObject *ppyRet = PyList_New(0);
        Py_ssize_t pyszLen = ppyRet ? PySequence_Length(ppyOthers) : -1;
        if (pyszLen >= 0)
        {
            Py_ssize_t sz;
            for (sz = 0; sz < pyszLen; sz++)
            {
                double dXB, dYB, dPXB, dPYB, dRB;
                PyObject *ppyB = PySequence_GetItem(ppyOthers, sz);
                if (!GetCircle(ppyB, &dXB, &dYB, &dPXB, &dPYB, &dRB))
                {
                    Py_XDECREF(ppyB);
                    return NULL;
                }
                else if (Collides(dXA, dXB, dYA, dYB, dPXA, dPXB, dPYA, dPYB,
                                  dRA, dRB))
                    PyList_Append(ppyRet, ppyB);
                Py_DECREF(ppyB);
            }
            return ppyRet;
        }
        else
            return NULL;
    }
    else
        return NULL;
}

static struct PyMethodDef s_apymeth[] = {
    {"overlaps", py_overlaps, METH_VARARGS, s_achOverlapsDoc },
    {"collides", py_collides, METH_VARARGS, s_achCollidesDoc },
    {"collides_all", py_collides_all, METH_VARARGS, s_achCollidesAllDoc },
    {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC init_collision(void)
{
    s_ppykX = PyString_FromStringAndSize(STR_AND_SIZE("x"));
    s_ppykY = PyString_FromStringAndSize(STR_AND_SIZE("y"));
    s_ppykPX = PyString_FromStringAndSize(STR_AND_SIZE("px"));
    s_ppykPY = PyString_FromStringAndSize(STR_AND_SIZE("py"));
    s_ppykRadius = PyString_FromStringAndSize(STR_AND_SIZE("radius"));

    if (s_ppykX && s_ppykY && s_ppykPX && s_ppykPY && s_ppykRadius)
        Py_InitModule3("bulletml._collision", s_apymeth, s_pchModDoc);
}
