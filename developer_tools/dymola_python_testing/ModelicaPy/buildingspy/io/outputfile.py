#Licensed under Apache 2.0 License.
#© 2020 Battelle Energy Alliance, LLC
#ALL RIGHTS RESERVED
#.
#Prepared by Battelle Energy Alliance, LLC
#Under Contract No. DE-AC07-05ID14517
#With the U. S. Department of Energy
#.
#NOTICE:  This computer software was prepared by Battelle Energy
#Alliance, LLC, hereinafter the Contractor, under Contract
#No. AC07-05ID14517 with the United States (U. S.) Department of
#Energy (DOE).  The Government is granted for itself and others acting on
#its behalf a nonexclusive, paid-up, irrevocable worldwide license in this
#data to reproduce, prepare derivative works, and perform publicly and
#display publicly, by or on behalf of the Government. There is provision for
#the possible extension of the term of this license.  Subsequent to that
#period or any extension granted, the Government is granted for itself and
#others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
#license in this data to reproduce, prepare derivative works, distribute
#copies to the public, perform publicly and display publicly, and to permit
#others to do so.  The specific term of the license can be identified by
#inquiry made to Contractor or DOE.  NEITHER THE UNITED STATES NOR THE UNITED
#STATES DEPARTMENT OF ENERGY, NOR CONTRACTOR MAKES ANY WARRANTY, EXPRESS OR
#IMPLIED, OR ASSUMES ANY LIABILITY OR RESPONSIBILITY FOR THE USE, ACCURACY,
#COMPLETENESS, OR USEFULNESS OR ANY INFORMATION, APPARATUS, PRODUCT, OR
#PROCESS DISCLOSED, OR REPRESENTS THAT ITS USE WOULD NOT INFRINGE PRIVATELY
#OWNED RIGHTS.
#!/usr/bin/env python
from buildingspy.thirdParty.dymat.DyMat import DyMatFile

def get_model_statistics(log_file, simulator):
    """ Open the simulation file ``log_file`` and return a dictionary
        with the model statistics.

        :log_file: The name of the log file.
        :simulator: The file format. Currently, the only supported
                    value is ``dymola``.

        With Dymola, a log file with the simulation statistics can
        be written using syntax such as

        >>> Advanced.TranslationInCommandLog := true;  #doctest: +SKIP
        >>> simulateModel(...);                        #doctest: +SKIP
        >>> savelog("simulator.log");                  #doctest: +SKIP

        This function returns a nested dictionary. The top level keys are
        ``initialization`` and ``simulation``, which contain the statistics
        for the initialization and the simulation problem.
        Note that not all models have an initialization problem, in which case
        the ``initialization`` dictionary is not present.

        Both dictionaries, if present, have the following keys
        if Dymola reported the corresponding statistic:

        - ``nonlinear``: The size of the nonlinear system of equations
          after the symbolic manipulation in the format ``2, 3, 1``.
        - ``linear``: The size of the linear system of equations
          after the symbolic manipulation.
        - ``numerical Jacobian``: The number of numerical Jacobians.
    """
    import os
    import re

    if simulator != "dymola":
        raise ValueError('Argument "simulator" needs to be set to "dymola".')

    if not os.path.isfile(log_file):
        raise IOError("File {} does not exist".format(log_file))

    with open(log_file) as fil:
        lines = fil.readlines();
        # Instantiate a dictionary that is used for the return value

        ret = {}
        dicIni = {}
        dicSim = {}

        reg = re.compile('\{(.*?)\}')

        CONSTA="Continuous time states:"
        NONLIN="Sizes after manipulation of the nonlinear systems:"
        LIN=   "Sizes after manipulation of the linear systems:"
        NUMJAC="Number of numerical Jacobians"
        TRAABO="Translation aborted"
        initalizationMode=False

        ret['translated'] = True
        for lin in lines:
            if lin.find(TRAABO) > 0:
                ret['translated'] = False
            elif lin.find(NONLIN) > 0:
                temp = lin.rpartition(":")[2]
                m = reg.search(temp)
                if initalizationMode:
                    dicIni['nonlinear'] = m.group(1)
                else:
                    dicSim['nonlinear'] = m.group(1)
            elif lin.find(LIN) > 0:
                temp = lin.rpartition(":")[2]
                m = reg.search(temp)
                if initalizationMode:
                    dicIni['linear'] = m.group(1)
                else:
                    dicSim['linear'] = m.group(1)
            elif lin.find(CONSTA) > 0:
                temp = lin.rpartition(":")[2].strip()
                temp = temp.partition("scalars")[0].strip()
                dicSim['number of continuous time states'] = temp
            elif lin.find(NUMJAC) > 0:
                temp = lin.rpartition(":")[2].strip()
                if initalizationMode:
                    dicIni['numerical Jacobians'] = temp
                else:
                    dicSim['numerical Jacobians'] = temp

            if lin.find("Initialization problem") > 0:
                initalizationMode=True


        if initalizationMode:
            ret["initialization"]=dicIni
        ret["simulation"]=dicSim
        return ret
    
def get_errors_and_warnings(log_file, simulator):
    """ Open the simulation file ``log_file`` and return a dictionary
        with the model warnings and errors.

        :log_file: The name of the log file.
        :simulator: The file format. Currently, the only supported
                    value is ``dymola``.

        With Dymola, a log file with the simulation statistics can
        be written using syntax such as

        >>> simulateModel(...);                        #doctest: +SKIP
        >>> savelog("simulator.log");                  #doctest: +SKIP
        
        This function returns a dictionary. The top level keys are
        ``warnings`` and ``errors``, which contain list of warning and 
        error messages.
    """
    
    import os

    if simulator != "dymola":
        raise ValueError('Argument "simulator" needs to be set to "dymola".')

    if not os.path.isfile(log_file):
        raise IOError("File {} does not exist".format(log_file))

    with open(log_file) as fil:
        lines = fil.readlines();
        # Instantiate lists that are used for the return value
        
        ret = {}
        listWarn = []
        listErr = []
    
        WARN="Warning:"
        ERR="... Error message from dymosim"
        
        for index, lin in enumerate(lines):
            if lin.find(WARN) >= 0:
                temp = lin.rpartition(":")[2].strip()
                listWarn.append(temp)
            elif lin.find(ERR) >= 0:
                listErr.append(lines[index+1].strip())
                
        ret["warnings"]=listWarn   
        ret["errors"]=listErr  
        return ret
    
class Reader:
    """Open the file ``fileName`` and parse its content.

    :param fileName: The name of the file.
    :param simulator: The file format. Currently, the only supported
                   value is ``dymola``.

    This class reads ``*.mat`` files that were generated by Dymola
    or OpenModelica.

    """

    def __init__(self, fileName, simulator):
        if simulator != "dymola":
            raise ValueError('Argument "simulator" needs to be set to "dymola".')

        self.fileName = fileName
        self._data_ = DyMatFile(fileName)


    def varNames(self, pattern=None):
        '''
           :pattern: A regular expression that will be used to filter the variable names.

           Scan through all variable names and return the variables
           for which ``pattern``, as a regular expression, produces a match.
           If ``pattern`` is unspecified, all variable names are returned.

           This method searches the variable names using the ``search`` function
           from `Python's re module <https://docs.python.org/2/library/re.html>`_.

           See also https://docs.python.org/2/howto/regex.html#regex-howto.

           Usage: Type

              >>> import os
              >>> from buildingspy.io.outputfile import Reader
              >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
              >>> r=Reader(resultFile, "dymola")
              >>> # Return a list with all variable names
              >>> r.varNames() #doctest: +ELLIPSIS
              [u'PID.I.y_start', u'PID.Td', u'PID.I.der(y)', ...]
              >>> # Return ['const.k', 'const.y']
              >>> r.varNames('const')
              [u'const.k', u'const.y']
              >>> # Returns all variables whose last character is u
              >>> r.varNames('u$')
              [u'PID.gainPID.u', u'PID.limiter.u', u'PID.gainTrack.u', u'PID.P.u', u'PID.I.u', u'gain.u']

        '''
        import re

        AllNames = self._data_.names()
        if pattern is None:
            return AllNames
        else:
            AllNamesFilt=[]    # Filtered variable names
            for item in AllNames:
                if re.search(pattern, item):
                    AllNamesFilt.append(item)
            return AllNamesFilt

    def values(self, varName):
        '''Get the time and data series.

        :param varName: The name of the variable.
        :return: An array where the first column is time and the second
                 column is the data series.

        Usage: Type
           >>> import os
           >>> from buildingspy.io.outputfile import Reader
           >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
           >>> r=Reader(resultFile, "dymola")
           >>> (time, heatFlow) = r.values('preHea.port.Q_flow')
        '''
        d = self._data_.data(varName)
        a = self._data_.abscissa(blockOrName=varName, valuesOnly=True)
        return a, d

    def integral(self, varName):
        '''Get the integral of the data series.

        :param varName: The name of the variable.
        :return: The integral of ``varName``.

        This function returns :math:`\int_{t_0}^{t_1} x(s) \, ds`, where
        :math:`t_0` is the start time and :math:`t_1` the final time of the data
        series :math:`x(\cdot)`, and :math:`x(\cdot)` are the data values
        of the variable ``varName``.

        Usage: Type
           >>> import os
           >>> from buildingspy.io.outputfile import Reader
           >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
           >>> r=Reader(resultFile, "dymola")
           >>> r.integral('preHea.port.Q_flow')
           -21.589191160164773
        '''
        (t, v)=self.values(varName)
        val=0.0;
        for i in range(len(t)-1):
            val = val + (t[i+1]-t[i]) * (v[i+1]+v[i])/2.0
        return val

    def mean(self, varName):
        '''Get the mean of the data series.

        :param varName: The name of the variable.
        :return: The mean value of ``varName``.

        This function returns

        .. math::

           \\frac{1}{t_1-t_0} \, \int_{t_0}^{t_1} x(s) \, ds,

        where :math:`t_0` is the start time and :math:`t_1` the final time of the data
        series :math:`x(\cdot)`, and :math:`x(\cdot)` are the data values
        of the variable ``varName``.

        Usage: Type
           >>> import os
           >>> from buildingspy.io.outputfile import Reader
           >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
           >>> r=Reader(resultFile, "dymola")
           >>> r.mean('preHea.port.Q_flow')
           -21.589191160164773
        '''
        t=self.values(varName)[0]
        r = self.integral(varName)/(max(t)-min(t))
        return r

    def min(self, varName):
        '''Get the minimum of the data series.

        :param varName: The name of the variable.
        :return: The minimum value of ``varName``.

        This function returns :math:`\min \{x_k\}_{k=0}^{N-1}`, where
        :math:`\{x_k\}_{k=0}^{N-1}` are the values of the variable ``varName``

        Usage: Type
           >>> import os
           >>> from buildingspy.io.outputfile import Reader
           >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
           >>> r=Reader(resultFile, "dymola")
           >>> r.min('preHea.port.Q_flow')
           -50.0
        '''
        v=self.values(varName)[1]
        return min(v)

    def max(self, varName):
        '''Get the maximum of the data series.

        :param varName: The name of the variable.
        :return: The maximum value of ``varName``.

        This function returns :math:`\max \{x_k\}_{k=0}^{N-1}`, where
        :math:`\{x_k\}_{k=0}^{N-1}` are the values of the variable ``varName``.

        Usage: Type
           >>> import os
           >>> from buildingspy.io.outputfile import Reader
           >>> resultFile = os.path.join("buildingspy", "examples", "dymola", "PlotDemo.mat")
           >>> r=Reader(resultFile, "dymola")
           >>> r.max('preHea.port.Q_flow')
           -11.284342
        '''
        v=self.values(varName)[1]
        return max(v)
